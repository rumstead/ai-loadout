# Session 2026-10-30-1815-5e1f0a2c

- Source: IMG_4762.MOV
- Captured: 2026-10-30 18:15 UTC
- Checksum: 5e1f0a2c00000000000000000000000000000000000000000000000000000000
- Pipeline: eval
- Swings: 2

## How to read this session

- Each `swing-NN/` folder is one swing, in the order hit.
- Start with `06-sequence.jpg`: the whole swing in one image, read left to right, top row then bottom row: address, takeaway, halfway back, top, transition, impact, follow-through, finish. Takeaway is a fixed short time before the top, about where the club is parallel to the ground, and halfway back is the hands reaching shoulder height, so those panels line up across swings. Transition and follow-through are the same short time before and after impact on every swing.
- `05-impact-zoom.jpg` is the ball area at full resolution for the frames just before, at, and after impact, top to bottom. Use it for contact, shaft lean, and strike.
- `07-after-shot.jpg` is a full-resolution frame a few seconds after impact. Its simulator screen shows this shot's numbers, which the Sim table below already has as text: look here for the cells the table leaves blank. Numbers visible in any other frame belong to the previous shot.
- `sim.json` in each swing folder is that swing's Sim table row with each number's vote count and when it first showed, and `"unchanged": true` when the screen did not change after the swing.
- `pose.csv` is the pose estimate as numbers, one row per sample (up to 60 a second): time in the video, ms from impact, the frame number in the swing, then x, y and visibility for the nose, shoulders, wrists, hips, knees, and heels. x and y are fractions of the frame width and height from the top left; empty cells mean no pose. Use it to measure hip turn, head movement, and hand height instead of estimating from the images.
- Every image has its position and its time in the video in the top-left corner.
- The Timing table gives takeaway start (the hands leaving address), top, and impact as frame numbers counted from 2.5s before impact with their time in the video, plus backswing and downswing time and tempo (backswing over downswing). When the hands are not seen at the top (out of frame) the top is not known and the durations are left blank.
- The skeleton lines on the sequence sheet are a pose estimate; trust the photo over the lines.
- Ball px/frame, Start dir and Grade come from following the ball in the swing video. Ball px/frame is how fast it leaves the club, in pixels per video frame, so compare it only within this session. Grade compares it to the session median: good is near the median or faster, poor is well under it, fair is between; `ball.json` in each swing folder has the thresholds. Start dir is sideways over up: negative starts left of the camera line, positive right. A `lost:` track says why the ball could not be followed, and that swing has no grade.

Ball flight: 2 good, 0 fair, 0 poor, 0 not tracked (median ball speed 23.4 px/frame)

| Swing | Impact | Strength | Hand speed peak | Ball px/frame | Start dir | Grade | Track |
|---|---|---|---|---|---|---|---|
| swing-01 | 2:25.4 | 0.83 | -8ms | 24.1 | 0.03 | good | ok |
| swing-02 | 3:12.3 | 0.41 | +25ms | 22.7 | -0.01 | good | ok |

## Sim

The numbers below are read off the simulator screen. A blank cell means the screen was covered or unreadable in most frames; check `07-after-shot.jpg` for those. A row of blanks can also mean the read failed, that the next swing started before this shot's numbers showed, or that the screen did not change after this swing (the simulator did not register a shot; `sim.json` has `"unchanged": true`). In the last two cases `07-after-shot.jpg` shows the previous shot.

| Swing | Club mph | Ball mph | Smash | Carry raw yd | Carry game yd | Total yd | Peak ft | Back spin | Total spin | Path | Face to path | Face to target |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swing-01 | 94.6 | 137.6 | 1.45 | 216.8 | | 226.6 | 95.8 | 3249 | 3322 | 2.5 I-O | 0.4 C | 2.1 O |
| swing-02 | | | | | | | | | | | | |
