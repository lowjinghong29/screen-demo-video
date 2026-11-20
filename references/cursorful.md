# Cursorful

Cursorful is a screen recorder that adds zooms which follow the cursor while you record, and then
opens an editor. This skill uses its free Chrome extension for web apps.

Everything in the first table was read from Cursorful's own pages and from the extension's
manifest (version 3.3.1) on 20 November 2026. The last section lists what has not been proven by
running it. When the screen disagrees with this file, believe the screen.

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

## The flow

1. The user installs the extension from the official listing and pins its icon.
2. Start a recording from the toolbar icon. Chrome shows its own "choose what to share" picker:
   pick the entire screen that holds the browser.
3. Chrome then shows a small "is sharing your screen" bar. Click *Hide*, or it sits in the picture.
4. Drive the app with `desktop.py`. Real mouse input is required: the extension draws its zooms
   from real clicks, and the recording shows the real cursor.
5. Plan the zooms with click pairs. Example: to zoom on an *Approve* button, click the row first
   and the button within three seconds. Single clicks spaced out for pacing get no zoom.
6. Stop from Cursorful's control. The editor opens.
7. In the editor: delete a zoom that lands on nothing, hide the browser frame, keep 16:9, export
   MP4. Leave the share link alone.
8. Take the newest `.mp4` from Downloads into the project's `rec/` folder and continue with
   `review.py beats` and `cut.py`. Do not add `target` or `zoom` to the shots: a 1080p export has
   no spare pixels, so a second zoom would only blur it.

## Not yet proven by running it

Treat these as likely, and check them on screen the first time:

- the exact names of the buttons in Cursorful's popup, recording control and editor;
- that the export lands in the Downloads folder (the site says "saved directly to your computer");
- how a native file picker looks inside the cropped recording.

If any step cannot be driven after two tries, ask the user to do that one click. Starting,
stopping and exporting take them under a minute in total.
