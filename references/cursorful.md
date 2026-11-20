# Cursorful

Cursorful is a screen recorder that adds zooms which follow the cursor while you record, and then
opens an editor. This skill uses its free Chrome extension for web apps.

The first table was read from Cursorful's own pages and from the extension's manifest (version
3.3.1) on 20 November 2026. The flow further down was driven for real that day, up to the export
panel. The last section lists what is still unproven. When the screen disagrees with this file,
believe the screen.

## Facts

| Topic | Fact | Source |
|---|---|---|
| Official listing | `https://chromewebstore.google.com/detail/cursorful/eihpmapodnppeemkhkbhikmggfojdkjd` | cursorful.com/install |
| Extension ID | `eihpmapodnppeemkhkbhikmggfojdkjd`. "Cursorful Go" is a different extension with a different ID. | Chrome Web Store |
| Browsers | Chrome, Edge and Brave on Windows, macOS and Linux. Not Firefox or Safari. | cursorful.com |
| Account | None needed to record and export. | features page |
| What it captures | The whole desktop, then it crops the result to the browser window. | home page FAQ |
| Auto-zoom trigger | Two or more clicks within three seconds. The zoom keeps following while clicks continue and eases out when they stop. | home page FAQ |
| Outside the browser | Recording continues, cropped to the browser, but follow-cursor and auto zooms do not work while another app has focus. Fixed zooms can be added in the editor. | home page FAQ |
| Pause and resume | Global shortcut `Ctrl+Shift+9`. It is the only shortcut the extension declares: there is none for start or stop. | extension manifest |
| Editor | Add, remove and adjust zooms on a timeline; choose a background; hide the tab strip, address bar and bookmarks; ten aspect ratios. | features page |
| Export | MP4 or GIF, rendered on this computer, 60 fps. Free plan up to 1080p, Pro up to 4K. No watermark and no time limit on either. | features page |
| Privacy | Videos never leave the computer unless you choose a share link or a cloud project. | home page FAQ |
| Microphone, webcam, captions | Can be tried, but exporting with them needs Pro. This skill does not use them: the voice is added afterwards by `cut.py`. | features page |
| Permissions it asks for | Read and change data on all sites, capture the screen, tabs, storage. | extension manifest |

## Licence and cost

- **Free plan: non-commercial use only.** Client work, marketing and anything the user is paid for
  needs **Cursorful Pro**: US$79 per seat, one-time payment (launch price seen on 20 November 2026;
  list price US$119). One seat covers commercial use for one user.
- Cursorful is proprietary software, not open source. Nothing from it is included in this
  repository. Each person installs it from the official store.
- If the user cannot or will not use it, record with `scripts/record.py` instead. That route is
  free and open source, and `cut.py` adds the zooms.

## The flow, as driven with desktop.py on 20 November 2026

A two-beat test on a local page was recorded and opened in the editor. Both click pairs produced a
zoom segment on the timeline, so real input from `desktop.py` triggers Cursorful's auto-zoom.

1. The user installs the extension from the official listing and pins its icon. The icon is a
   green square with a white pointer; its tooltip reads *Cursorful - Screen Recorder with Auto Zoom*.
2. Click the icon. There is no popup: a pinned tab opens at `record.html`, titled *Cursorful -
   Start recording*, with the heading *Record your browser in three simple steps*.
3. **01 Share this screen** has three cards: screen, microphone, camera.
   - The microphone is on by default and shows a live waveform. Open the card's menu and choose
     *Disable microphone*. The camera card greys out with it.
   - Click *Select screen*. Chrome shows *Share your entire screen*, with one *Entire screen*
     thumbnail, an *Also share system audio* switch (off), and *Share* / *Cancel*. *Share* is
     disabled until the thumbnail is clicked.
4. **02 Hide screen sharing bar.** Chrome puts a bar at the bottom of the screen: "Cursorful -
   Screen Recorder with Auto Zoom is sharing your screen", with *Stop sharing* and *Hide*. Click
   *Hide*, or it is in the picture.
5. **03 Start recording** is below the fold. Its text: "You will be taken to your previous tab and
   recording will start immediately. Stop the recording from this pinned tab or by pressing
   Cursorful's button in the extensions toolbar."
6. Drive the app with `desktop.py`. Plan the zooms with click pairs. Example: to zoom on an
   *Approve* button, click the row first and the button within three seconds.
7. Click the toolbar icon again to stop. The editor opens in a tab titled *Editor | Cursorful*.
   The preview shows the app inside a clean window frame on a background image; the real tab
   strip and any browser banner are not shown.
8. *Export video* (top right) opens a panel: *Local*, *GIF*, *Link*; *Hide Cursorful icon*;
   resolution (1080p); a quality slider.
9. **On the free plan the panel has a checkbox:** "I confirm that this video is for non-commercial
   use. I understand that commercial or corporate use without a Pro license is unlawful…" This is
   a legal declaration. An agent must never tick it. The user ticks it if it is true, or activates
   Pro.
10. Move the exported `.mp4` into the project's `rec/` folder and continue with `review.py beats`
    and `cut.py`. Do not add `target` or `zoom` to the shots: a 1080p export has no spare pixels,
    so a second zoom would only blur it.

What to know while driving:

- Chrome's toolbar and the share dialog are **not** in the Snapshot tree. Find them on a frame.
  The pages inside the tab (start page, editor) are in the tree with `"use_dom": true`.
- Everything is recorded from the moment *Start recording* is clicked, including the time you
  spend looking things up. A two-beat test came out 1 min 40 s long because of that. Collect
  coordinates first, and pause with `Ctrl+Shift+9` when you must look.
- The start page suggests setting a keyboard shortcut for *Activate the extension* under
  Extensions > Keyboard shortcuts. If the user sets one, starting and stopping no longer depend on
  finding the icon.
- A Snapshot taken right after a tab closes can still list the old tab's buttons. When a Snapshot
  contradicts what you expect, check a frame.
- Each recording stays in Cursorful's local project list (*Load a recording*) until it is deleted there.

## Not yet proven by running it

- Where the exported file is saved. The site says "saved directly to your computer"; look in
  Downloads first.
- The export panel with a Pro licence active (presumably without the checkbox).
- The pause shortcut during a take.
- How a native file picker looks inside the cropped recording.

If any step cannot be driven after two tries, ask the user to do that one click.
