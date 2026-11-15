import type { EngineInterface } from 'claude-code'

type Marketplaces = Record<string, { source?: { source?: string }; installLocation?: string }>

const FETCH_MS = 10_000

// The marketplace an installed plugin came from, read off its cache directory,
// `<config>/plugins/cache/<marketplace>/<plugin>/<version>`.
export function marketplaceOf(root: string): string | undefined {
  return root.match(/\/plugins\/cache\/([^/]+)\/[^/]+\/[^/]+\/?$/)?.[1]
}

async function git(
  $: EngineInterface,
  dir: string,
  args: string[],
  timeoutMs?: number,
): Promise<string | undefined> {
  const ran = await $.process
    .run(['git', '-C', dir, ...args], { env: { GIT_TERMINAL_PROMPT: '0' }, timeoutMs })
    .catch(() => undefined)
  return ran?.exitCode === 0 ? ran.stdout.trim() : undefined
}

// The checkout this plugin is served from: the directory a local marketplace
// points at, or the one holding the plugin when it is loaded in place.
async function sourceCheckout($: EngineInterface, configDir: string): Promise<string | undefined> {
  const marketplace = marketplaceOf($.plugin.root)
  if (marketplace === undefined) return git($, $.plugin.root, ['rev-parse', '--show-toplevel'])

  const known = JSON.parse(
    String(await $.fs.read(`${configDir}/plugins/known_marketplaces.json`)),
  ) as Marketplaces
  const entry = known[marketplace]
  if (entry?.source?.source !== 'directory' || !entry.installLocation) return undefined

  return git($, entry.installLocation, ['rev-parse', '--show-toplevel'])
}

// One line saying the checkout is behind its upstream and how to catch up, or
// undefined when it is current, has no upstream, or is not a local checkout.
// Fetches first, for at most FETCH_MS; a failed fetch leaves the last one's refs.
export async function staleCheckoutLine(
  $: EngineInterface,
  configDir: string,
): Promise<string | undefined> {
  const checkout = await sourceCheckout($, configDir).catch(() => undefined)
  if (checkout === undefined) return undefined

  await git($, checkout, ['fetch', '--quiet'], FETCH_MS)
  const names = await git($, checkout, ['rev-parse', '--abbrev-ref', 'HEAD', '@{upstream}'])
  const behind = Number(await git($, checkout, ['rev-list', '--count', 'HEAD..@{upstream}']))
  if (names === undefined || !(behind > 0)) return undefined

  const [branch, upstream] = names.split('\n')
  const repo = checkout.split('/').pop()
  const commits = behind === 1 ? '1 commit' : `${behind} commits`
  return (
    `${repo} ${branch} is ${commits} behind ${upstream}; installed skills are stale. ` +
    `Run git -C ${checkout} pull --ff-only.`
  )
}
