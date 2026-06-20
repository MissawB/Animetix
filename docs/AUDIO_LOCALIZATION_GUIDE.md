# Audio Assets Localization Guide

This document guides you step-by-step through resolving `403 (Forbidden)` errors when loading audio files from `mixkit.co`. These errors are typically caused by hotlinking protection (blocking direct embedding of files from another website). The solution is to host these files directly within your project.

---

## Steps to Follow:

### Step 1: Create the Sound Effects Directory

You must create a new directory inside your project to store the audio files.

1. Open your file explorer (Windows) or Finder (macOS) and navigate to the root of your project.
2. Go to the `frontend/public` directory.
3. Create a new directory named `sfx` inside `frontend/public`.

   The full path to the directory should be: `frontend/public/sfx`

### Step 2: Download the MP3 Audio Files

Click on each link below to download the MP3 files. Make sure to save them with the specified filenames.

1. **For the 'click' sound:**
   * Link: `https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3`
   * Save as: `2571-preview.mp3`

2. **For the 'win' sound:**
   * Link: `https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3`
   * Save as: `1435-preview.mp3`

3. **For the 'loss' and 'error' sounds:**
   * Link: `https://assets.mixkit.co/active_storage/sfx/2513/2513-preview.mp3`
   * Save as: `2513-preview.mp3`

4. **For the 'unlock' sound:**
   * Link: `https://assets.mixkit.co/active_storage/sfx/2019/2019-preview.mp3`
   * Save as: `2019-preview.mp3`

5. **For the 'reveal' sound:**
   * Link: `https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3`
   * Save as: `2568-preview.mp3`
   *(Note: The original implementation contained an incorrect link; this is the correct file for 'reveal'.)*

### Step 3: Move the Files to the Project Directory

Once all the MP3 files are downloaded, move them into the `sfx` directory you created in Step 1.

* Ensure the files are placed directly under `frontend/public/sfx`.

### Step 4: Restart the Frontend Development Server

For your application to detect these new local files, you need to restart your frontend development server.

1. Stop your frontend server (typically by pressing `Ctrl+C` in the terminal where it is running).
2. Restart the server (e.g., using `npm run dev` or `yarn dev`, depending on your configuration).

---

## Verification

After completing these steps:

* Navigate to your application in the browser.
* Open the developer console (F12) and inspect the "Console" and "Network" tabs.
* The `403 (Forbidden)` errors for the audio files from `mixkit.co` should no longer occur. The sounds should load and play correctly.

If you encounter any issues, please let me know.