---
name: golf-swing-analysis
description: Analyze golf swings from uploaded videos or from golf-etl session folders in a GitHub repo. Use this skill whenever the user uploads a golf swing video (.mov, .mp4, or similar) and asks for coaching feedback, swing analysis, what they're doing wrong, how to improve, or any question about their golf swing mechanics. Also use it whenever the user asks to review a golf session, their latest or recent swings, today's range session, or a folder under sessions in their golf-etl sessions repo, even if they don't say golf-etl. Also use it for a session's simulator or launch monitor numbers, even a quick lookup. Also trigger when the user says they're at the range and wants swing feedback, or when they share multiple swing videos for comparison. Get the frames (from the session folder or by extracting them from the video), identify the camera angle, ask for ball flight context before diagnosing, and deliver structured coaching feedback with prioritized next steps.
license: MIT
compatibility: Uploaded videos need a shell with ffmpeg. golf-etl sessions need access to the GitHub repo that holds them.
metadata:
  version: "0.6.0" # x-release-please-version
---

# Golf Swing Analysis Skill

A structured coaching workflow for analyzing golf swings from any camera angle, with calibrated confidence and prioritized feedback. Frames come either from a golf-etl session or from a video the user uploads.

---

## Core Principles (from real coaching sessions)

1. **Camera angle first**: state what the angle allows and doesn't allow before diagnosing anything
2. **Ball flight is ground truth**: ask for it before making path/face claims
3. **One root cause, not a list**: most swing faults cascade from one problem; identify it
4. **Compensations are not faults**: early extension, flipping, and chicken wing are usually symptoms, not causes
5. **Calibrate confidence**: say "clearly visible", "likely", or "hard to confirm from this angle" on every call
6. **Strengths first**: always lead with what's working before observations
7. **One priority to fix**: give the golfer one thing to work on, not five

---

## Context

If `~/.agents/context/golf-swing-analysis.md` exists, read it first. It says where the golfer's golf-etl sessions live, and can give their handicap, usual miss, and what they are working on. Anything in it overrides the defaults below, and a question it already answers does not get asked in Step 3. `context.example.md` shows the fields.

For a golf-etl session, also read `golfer.md` at the root of the sessions repo when it is there. It is the golfer's own file, with the same handicap, usual miss and working-on fields plus a `## Log` of past sessions, and it is how a chat without the context file (claude.ai) gets them. Where the two disagree, `golfer.md` wins. `golfer.example.md` shows its layout.

---

## Step 1: Get the Frames

There are two sources. Use 1A when the user mentions a session or their latest or recent swings. Use 1B when they upload a video.

### 1A: From a golf-etl session

[golf-etl](https://github.com/rumstead/golf-etl) turns each range video into a session folder with frames already picked, labeled, and in order. Sessions live under `sessions/` in a GitHub repo. The context names the repo; otherwise ask.

1. **Find the session.** If the repo is not in the chat, ask the user to add it (in claude.ai, **+ > Add from GitHub**), then list `sessions/`. Folder names start with the capture date and time (`YYYY-MM-DD-HHMM-<id>`), so the newest name is the latest session. Use the session the user names if they name one.
2. **Read `session.md` first.** It lists the swings with their impact times, a Ball flight table, the Sim, Timing, Body and By grade tables when the session has them, sounds that were rejected as not being a swing, and how to read the files. Its `Source:` line names the original video, and on newer sessions its `Club:` line is the club the golfer picked when uploading. Then read `sessions/index.md`, one row of medians per session, `sessions/chain.md` (step 10) if it exists, and `golfer.md` at the repo root if it exists.
3. **Know the files.** Each swing has `06-sequence.jpg`, `05-impact-zoom.jpg`, and `07-after-shot.jpg`, and there are no clips. Older sessions keep an older file set: they may have `01-address.jpg` to `04-finish.jpg` instead of the sequence sheet, may lack `pose.csv` and the Timing, Body and By grade tables, may draw the pose as green lines on the sequence panels (trust the photo over the lines), and their `session.md` may mention a `clip.mp4` that does not exist. Use what is there.
4. **Choose the swings.** Leave out a swing as a practice swing only when the simulator did not register a shot (`sim.json` has `"unchanged": true`), or, on a session without a Sim table, when its impact zoom shows no ball. A Ball flight track of `lost: no ball launched` does not by itself mean no ball was hit: the tracker misses the ball on some videos, and a swing with Sim numbers was a shot. When the session's `Club:` is `mixed`, the golfer hit several clubs: ask which swings were which club, and compare swings, grades and the By grade table only within one club, since grades are against the whole session's median. Then build contact sheets of every remaining swing's takeaway panel and impact frame, because hinge and strike are read on all of them (steps 5 and 6). For the deeper read of full sequences, take all of them if there are 5 or fewer. Otherwise use the Ball flight grades to pick: the best and worst graded swings plus a few in between, so the read compares good and bad strikes. Without grades, take 5 spread across the session (the first, the last, and evenly in between). The user's choice of swings always wins. If the golfer changed something mid-session, compare the swings before and after that point.
5. **For each chosen swing, view `swing-NN/06-sequence.jpg` first.** It is the whole swing in one image, read left to right, top row then bottom row: address, takeaway, halfway back, top, transition, impact, follow-through, finish. Takeaway is the hands reaching hip height and halfway back the hands reaching shoulder height, so those panels are the same body position on every swing. Each panel is labeled with the position and its time in the video, and every panel of a swing is the same crop around the golfer, the club and the ball. **Read hinge on the takeaway panel for every swing:** find the hands, then the clubhead. Hanging means the head is near the knee with the shaft below the hands, so there is no hinge yet. Set means the shaft looks short because it points at the camera, or the head is at hand height or above. A head left of the hands is inside them, and a camera behind the golfer exaggerates that. Check `session.md` first: takeaway falls back to a fixed time before the top when the hips are not in the pose, and those panels do not compare. Report how many swings show each look and the average smash of each.
6. **Then view `swing-NN/05-impact-zoom.jpg`.** It is the ball area for the frames just before, at, and just after impact, top to bottom. Use it for contact, and for shaft lean only when the camera is face-on (down the line the shaft leans along the line of sight), and **read strike location on every swing:** in the impact row (labeled contact on newer sessions), place the ball center along the face from hosel to toe and call it toe, center, or heel. Do not say this view cannot show strike without checking the frames. If the ball has already left in that frame, or the club is still short of the ball, mark the swing unreadable. Newer sessions also have a `Strike` column in the Ball flight table: the ball's center from the shaft's line in ball diameters, larger toward the toe. It ranks the swings of one session and is not inches on the face. Use it to order the swings and to check your read; when the two disagree, say so and go with the frame. A blank Strike cell means the pipeline could not measure that swing, not that it was centered. A centered strike with low smash, low peak height, and low spin is thin, not a toe.
7. **If there is a simulator or launch monitor screen, use the Sim table in `session.md` first.** golf-etl reads the screen off the video: club speed, ball speed, smash, carry, total, peak height, back and total spin, club path, face to path, and face to target, and on newer sessions side spin, launch (VLA), side launch (HLA) and offline from the screen's left panel, where negative is left. Those four are blank more often because the golfer stands in front of that panel. Use them to tell a strike miss from a face miss: side spin that curves the ball more than face to path explains, with low smash, points at the strike (toe or heel) and not the face. `swing-NN/sim.json` holds the same row. A blank cell means the number could not be read confidently. A blank row can mean the read failed, that the next swing started before this shot's numbers showed, or that the screen did not change after the swing (`sim.json` has `"unchanged": true`). In the last two cases `07-after-shot.jpg` shows the previous shot, so take no numbers for that swing. For other blank cells, for numbers the table does not have (launch, side spin and offline on older sessions), and for sessions without a Sim table, read `swing-NN/07-after-shot.jpg`. It is taken a few seconds after impact, when the screen shows this shot's numbers, but carry (game) and total length count up for about 13s after impact while the ball flies and rolls, so this frame can show them short. Take those two from the Sim table only: when the table leaves them blank, say they were not read. Read what is clearly legible: club path, face to path, face to target, club speed, ball speed, smash factor, launch (VLA/HLA), spin (back, side, total), carry, offline, peak height. Only report digits you can actually read; if part of the panel is hidden behind the golfer or blurred, say which numbers you could not read rather than guessing. **Numbers in the address, impact, or sequence frames belong to the previous shot, so never attribute them to the current swing.** They are useful one way: the left column (launch, side spin, offline) is usually hidden in `07-after-shot.jpg` but legible in the next swing's address panel. Confirm it is the right shot by matching its back spin and peak height.
8. **Use the numbers in `session.md` and the swing folder instead of estimating from pictures.**
   - Ball flight table: `Grade` (good, fair, poor) is strike quality relative to the session median, not distance. The summary line gives its basis: sim smash on sim sessions, px/frame otherwise. px/frame is unreliable indoors, so use sim ball speed when both exist. Smash is ball speed over club speed, so it moves with the sim's club speed read: when a swing's smash and its ball speed and carry disagree about how well it was struck, say so and lean on ball speed and carry. `Start dir` is negative left of the camera line, positive right. Speeds only compare within one session.
   - Timing table: backswing time, downswing time, and tempo (backswing over downswing) per swing. The takeaway start is the club leaving the ball. A start marked `hands` was timed off the hands instead and reads late down the line, so leave that swing's backswing and tempo out of comparisons, as older sessions' are throughout. Compare tempo across swings in the session (does it change on the poor grades?) rather than against a fixed ratio. A blank row means the hands left the frame at the top.
   - Body table: how far the head, hips and hands moved from address at the top and at impact, the hands' height over the shoulders at the top, and the spine's lean at address and impact, in leg lengths and degrees. `View` is the camera angle the pipeline saw. Down the line, side is toward the ball, so hips moving toward the ball at impact is early extension and hands moving up or toward the body at impact changes where the face meets the ball. Face-on, side is to the right of the picture. The pose is an estimate: read a measure across swings, and check a surprising value against the photo.
   - By grade table: the mean of every Sim, Timing and Body number over the good, fair and poor swings. Start here when looking for a cause. A number that is the same on good and poor swings is not the cause, however it looks in the pictures.
   - `swing-NN/pose.csv`: joint positions per sample, as fractions of the frame from the top left. Frame numbers count from 2.5s before impact. Open it only for a measure the Body table does not have, or on a session without one.
9. **Use `sessions/index.md` for progress.** Compare this session's medians with earlier sessions at the same `Venue`, and say which way the numbers tied to what the golfer is working on have moved. Sessions differ in club and day, so call a trend only when it holds over more than one session.
10. **Use `sessions/chain.md` before naming a cause.** It pools every down-the-line swing of one club across sessions, each number taken against its own session's median, and ranks every measure against ball speed and against strike. A measure near 0 there does not move with how the ball was struck over many swings, so it is a weak root cause however it looks in one session. One near +1 or -1 is a candidate to check in the frames, not a proof. Read the swing and session counts beside each value: a value from few swings or one or two sessions is weak, and the second table marks counts under 10 as too few to read. When `Swing order` moves with ball speed, the golfer warmed up through the sessions, and anything else that drifted during a session can look tied to ball speed. Each club repeats its tables for recent sessions; when the golfer is working on a change, read those first. The takeaway rows come from the golfer's own labels in `sessions/takeaway-labels.csv`. Your hinge read from step 5 is not a label, so never write that file. Mixed-club sessions are left out of `chain.md`.
11. **Look across swings.** Swings in one session are usually the same club and setup. Base the read on what repeats, and point at a single swing (by its folder name, like `swing-03`) only when it differs. Compare pose and panels only with sessions at the same `Venue`. Before naming a cause, check in the By grade table (or by hand on a session without one) that the measure actually separates the good swings from the bad ones, and in `chain.md` that it does so across sessions: a fault present on both is not the cause. Say what the session could not measure.

Then continue with Step 2. Do not run ffmpeg for a session; the frames are already chosen.

### 1B: From an uploaded video

Use ffmpeg to extract frames at 8fps from each uploaded video into a scratch directory. Scale to 960x540 for speed.

```bash
mkdir -p swing_frames/<video_id>
ffmpeg -i <video_path> \
  -vf "fps=8,scale=960:540" \
  swing_frames/<video_id>/frame_%03d.jpg \
  -y -loglevel quiet
```

Get total frame count and duration to know which frames to pull:
```bash
ffprobe -v quiet -show_entries format=duration -of default <video_path>
```

For each video, view these key positions (adjust frame numbers based on duration):
- Address/setup: early frames
- Takeaway: ~25% through
- Mid-backswing: ~35%
- Top of backswing: ~45-50%
- Early downswing/transition: ~55%
- Impact zone: ~65-70%
- Follow-through: ~80%
- Finish: final frames

---

## Step 2: Identify Camera Angle

Before any diagnosis, determine the camera angle and state it explicitly. On a golf-etl session the Body table's `View` column says what the pipeline saw from the feet; confirm it against the frames.

**True Face-On**: Camera pointing directly at the golfer's chest at address. Shows: weight transfer, lateral sway and slide, shoulder tilt, shaft lean at impact. Does NOT show: swing plane, club path, early extension.

**True Down-the-Line (DTL)**: Camera pointing directly down the target line from behind. Shows: swing plane, club path above/below plane, over-the-top, flat/steep, early extension (hips moving toward the ball), posture. Does NOT show: lateral sway, weight transfer direction, shaft lean at impact.

**In-Between / Oblique**: Most range videos. State clearly: "This angle is between face-on and DTL. I can see [X] reliably but [Y] is harder to confirm. Ball flight will help verify."

**High/Low**: Note if the camera is significantly above or below hip height, as this distorts plane readings.

Do NOT make confident plane or path calls from a non-DTL angle. Do NOT make confident weight transfer calls from a non-face-on angle.

---

## Step 3: Ask for Context (Before Diagnosing)

After identifying the angle, ask the golfer these questions before delivering full analysis. This is not optional: ball flight resolves ambiguity that camera angle cannot:

```
Before I give you the full read, a few quick questions:
1. What club is this?
2. What does the ball typically do: pull, slice, push, draw, something else?
3. What have you already been told or are you already working on?
4. Did you change anything during the session, and at which swing?
```

Drop any question the context, `golfer.md` or `session.md` already answers (its `Club:` line answers the first, except `mixed`), and say what you took from it ("you're working on X, so I'll read with that in mind"). The golfer's latest lesson and anything they say they changed outrank findings from older sessions.

If the user is at the range and wants quick feedback, you can deliver a preliminary visual read while waiting for their answers, but clearly label it as "preliminary" and revisit after they answer.

For a golf-etl session, ask once for the whole session, not once per swing. The Ball flight grades already say which swings were struck well, so ask about the shape of the ball flight (start line and curve), not about contact.

When the Sim table or `07-after-shot.jpg` shows simulator or launch monitor numbers, those numbers are the ball flight: use club path, face to path, and face to target to settle path and face questions (for example, a positive club path with a closed face to path is a draw or hook pattern) and do not ask the golfer to describe ball flight for those swings. Still ask which club and what they are working on. Tie every diagnosis back to both the frames and the numbers, and say when they disagree.

---

## Step 4: Deliver Structured Analysis

Structure the output as follows:

### Since Last Time
Only for a golf-etl session with an earlier log entry. Find the latest entry before this session in the `## Log` of `golfer.md`, in your memory of this project, or in the context, in that order. Open with what it set as the priority and how its measure has moved: take that session's value and today's from `sessions/index.md` or the two `session.md` files, never from the entry or from memory, which can blur a number. One or two sentences, for example "Last time (2026-11-08) the priority was the face closing through impact: face to path was 2.4 closed, today 1.8." Say plainly when it did not move or got worse, and when the sessions do not compare (another venue, or a number one of them lacks). With no entry, skip this section.

### Camera Angle & Confidence
State the angle and what it allows/limits in 2-3 sentences.

### Strengths
List 2-4 genuine positives. Look for:
- Setup/posture quality
- Weight transfer direction and completeness
- Lower body sequencing
- Shoulder turn
- Finish position
- Rhythm and tempo

Do not invent positives. If something is genuinely neutral, leave it out.

### Key Observations
List the 1-3 most significant issues visible from this angle. For each:
- State what you see ("the right shoulder fires toward the target at the start of the downswing")
- State your confidence level ("clearly visible from this angle" / "likely but hard to confirm without DTL" / "ball flight suggests this")
- Do NOT state a compensation as a primary fault

**Common fault cascade to watch for (do not invert):**
- Steep/outside-in path → early extension (hips thrust to move low point) → flip/scoop (hand release to close face)
- The path is the cause. Early extension and flip are almost always downstream.
- Over-the-top typically lives in the TRANSITION (right shoulder firing), not the backswing
- Arm-dominated backswing is often overstated. Look for it but confirm before calling it

### Root Cause
Name the single most upstream fault causing the cascade. This is the one thing fixing everything else.

### One Thing to Work On
Give one drill or feel for the root cause. Not two. Not three. One.

Format:
- **The problem**: what's happening
- **The drill**: specific, concrete, executable at the range
- **The feel**: what it should feel like differently
- **What gets better**: what downstream issues will improve as a result

### What to Leave Alone
Explicitly name 1-2 things the golfer should NOT tinker with. This prevents over-coaching and rabbit holes.

### Log
For a golf-etl session, end with one log line so the next review can pick up from this one:

```
- 2026-11-14 (sim, 7 iron): priority <the one thing>. Measure: <a column in session.md or index.md>, <today's value>.
```

The date, venue and club come from `session.md`, the club from the golfer when `session.md` has no `Club:` line or says `mixed`. Pick a measure the pipeline writes, so the next session has the same number to compare. Then keep the entry, by the first of these that you can do:

1. If you can write to the sessions repo (a shell with push access), append the line under `## Log` in `golfer.md` and commit it.
2. If the chat has memory you can write to, save or update a single memory titled "golf coaching log" that holds the log lines, newest last, and tell the golfer you did. Keep the priority and the measure's name in it; the numbers get re-read from the repo.
3. Otherwise ask the golfer to paste the line under `## Log` in `golfer.md`.

Always show the line, whichever of these you did.

---

## Step 5: Handle Pushback

If the golfer pushes back on a call:
1. Go back to the specific frames immediately. Do not defend from memory
2. Re-examine the relevant position with fresh eyes
3. If they're right, correct clearly: "You're right. Looking again at [frame], [corrected read]. I'll pull back what I said about [X]."
4. Update the root cause and priority if the correction changes the picture
5. Never defend an incorrect call to preserve consistency

---

## Angle-Specific Limitations Reference

| What You're Trying to Assess | Best Angle | Fallback |
|------------------------------|-----------|---------|
| Swing plane / club above or below plane | DTL | Ask about ball flight (slice = steep/over-top) |
| Over-the-top move | DTL | Look for low finish, hands exiting left |
| Early extension (hips toward the ball) | DTL | Face-on shows the golfer standing up through impact |
| Lateral sway on backswing | Face-on | Hard to confirm from DTL |
| Weight transfer direction | Face-on | Look at trail foot at finish |
| Shoulder tilt at address | Face-on | N/A |
| Shaft lean at impact | Face-on | N/A |
| Grip | Either close-up | Ask player |

---

## Handicap Context

Calibrate feedback to the player's level, from the context when it gives a handicap:

**20+ handicap**: Path and contact are the priorities. Grip, posture, and pivot only if they're the direct root cause. Don't add swing thoughts; remove them.

**10-20 handicap**: Path is usually solid or near-solid. Look at transition, shaft lean, and release pattern. One ball-striking variable at a time.

**Under 10**: Precision matters. Plane, attack angle, face control, and sequencing timing. Subtle feels are appropriate.

---

## Red Flags (Things Often Misdiagnosed)

- **Flip at impact** → almost always a compensation for steep path, not a standalone fault. Fix the path.
- **Early extension** → almost always a compensation for steep path or loss of posture. Fix the root.
- **Short/low finish** → symptom of outside-in path and/or deceleration, not a cause.
- **Arm-dominated backswing** → often over-called. Confirm with good shoulder turn evidence before diagnosing.
- **C-posture** → check carefully before calling. Camera angle and clothing can make good posture look rounded.
- **Over-the-top** → the move happens in the transition (right shoulder), not necessarily because the takeaway is bad.

---

## Output Tone

- Direct, practical, no fluff
- Whenever you name a swing from a session, also give its source video and the time to scrub to, from that swing's Impact time in `session.md`, for example "`swing-07`, scrub to 12:07 in `IMG_4601`". The golfer checks your read against the original video that way; there are no clips
- One coach talking to one golfer, not a written report
- No bullet point overload; use prose where it flows better
- End with a clear "here's what to do at the range today" statement
