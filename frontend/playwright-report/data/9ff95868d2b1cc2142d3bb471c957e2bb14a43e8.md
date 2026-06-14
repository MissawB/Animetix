# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: a11y.spec.ts >> Audit d'Accessibilité (a11y) >> Vérification WCAG sur la route : /static/
- Location: e2e\a11y.spec.ts:15:5

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -   1
+ Received  + 367

- Array []
+ Array [
+   Object {
+     "description": "Ensure buttons have discernible text",
+     "help": "Buttons must have discernible text",
+     "helpUrl": "https://dequeuniversity.com/rules/axe/4.11/button-name?application=playwright",
+     "id": "button-name",
+     "impact": "critical",
+     "nodes": Array [
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": null,
+             "id": "button-has-visible-text",
+             "impact": "critical",
+             "message": "Element does not have inner text that is visible to screen readers",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-label",
+             "impact": "critical",
+             "message": "aria-label attribute does not exist or is empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-labelledby",
+             "impact": "critical",
+             "message": "aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": Object {
+               "messageKey": "noAttr",
+             },
+             "id": "non-empty-title",
+             "impact": "critical",
+             "message": "Element has no title attribute",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "implicit-label",
+             "impact": "critical",
+             "message": "Element does not have an implicit (wrapped) <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "explicit-label",
+             "impact": "critical",
+             "message": "Element does not have an explicit <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "presentational-role",
+             "impact": "critical",
+             "message": "Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+             "relatedNodes": Array [],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element does not have inner text that is visible to screen readers
+   aria-label attribute does not exist or is empty
+   aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
+   Element has no title attribute
+   Element does not have an implicit (wrapped) <label>
+   Element does not have an explicit <label>
+   Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+         "html": "<button class=\"text-3xl hover:rotate-90 transition-transform duration-300 text-black dark:text-white\">",
+         "impact": "critical",
+         "none": Array [],
+         "target": Array [
+           "#manga-sidebar > .mb-12.justify-between.items-center > .hover\\:rotate-90.text-3xl.duration-300",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": null,
+             "id": "button-has-visible-text",
+             "impact": "critical",
+             "message": "Element does not have inner text that is visible to screen readers",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-label",
+             "impact": "critical",
+             "message": "aria-label attribute does not exist or is empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-labelledby",
+             "impact": "critical",
+             "message": "aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": Object {
+               "messageKey": "noAttr",
+             },
+             "id": "non-empty-title",
+             "impact": "critical",
+             "message": "Element has no title attribute",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "implicit-label",
+             "impact": "critical",
+             "message": "Element does not have an implicit (wrapped) <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "explicit-label",
+             "impact": "critical",
+             "message": "Element does not have an explicit <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "presentational-role",
+             "impact": "critical",
+             "message": "Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+             "relatedNodes": Array [],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element does not have inner text that is visible to screen readers
+   aria-label attribute does not exist or is empty
+   aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
+   Element has no title attribute
+   Element does not have an implicit (wrapped) <label>
+   Element does not have an explicit <label>
+   Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+         "html": "<button class=\"text-3xl hover:rotate-90 transition-transform duration-300 text-black dark:text-white\">",
+         "impact": "critical",
+         "none": Array [],
+         "target": Array [
+           "#settings-drawer > .mb-12.justify-between.items-center > .hover\\:rotate-90.text-3xl.duration-300",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": null,
+             "id": "button-has-visible-text",
+             "impact": "critical",
+             "message": "Element does not have inner text that is visible to screen readers",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-label",
+             "impact": "critical",
+             "message": "aria-label attribute does not exist or is empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "aria-labelledby",
+             "impact": "critical",
+             "message": "aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": Object {
+               "messageKey": "noAttr",
+             },
+             "id": "non-empty-title",
+             "impact": "critical",
+             "message": "Element has no title attribute",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "implicit-label",
+             "impact": "critical",
+             "message": "Element does not have an implicit (wrapped) <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "explicit-label",
+             "impact": "critical",
+             "message": "Element does not have an explicit <label>",
+             "relatedNodes": Array [],
+           },
+           Object {
+             "data": null,
+             "id": "presentational-role",
+             "impact": "critical",
+             "message": "Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+             "relatedNodes": Array [],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element does not have inner text that is visible to screen readers
+   aria-label attribute does not exist or is empty
+   aria-labelledby attribute does not exist, references elements that do not exist or references elements that are empty
+   Element has no title attribute
+   Element does not have an implicit (wrapped) <label>
+   Element does not have an explicit <label>
+   Element's default semantics were not overridden with role=\"none\" or role=\"presentation\"",
+         "html": "<button class=\"fixed bottom-6 left-6 w-14 h-14 bg-black text-yellow-400 dark:bg-[#0f0f1a] dark:text-white rounded-2xl shadow-2xl flex items-center justify-center text-3xl rotate-45 hover:rotate-0 transition-all duration-500 z-[800] group border border-black/10 dark:border-white/10\">",
+         "impact": "critical",
+         "none": Array [],
+         "target": Array [
+           ".left-6",
+         ],
+       },
+     ],
+     "tags": Array [
+       "cat.name-role-value",
+       "wcag2a",
+       "wcag412",
+       "section508",
+       "section508.22.a",
+       "TTv5",
+       "TT6.a",
+       "EN-301-549",
+       "EN-9.4.1.2",
+       "ACT",
+       "RGAAv4",
+       "RGAA-11.9.1",
+     ],
+   },
+   Object {
+     "description": "Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds",
+     "help": "Elements must meet minimum color contrast ratio thresholds",
+     "helpUrl": "https://dequeuniversity.com/rules/axe/4.11/color-contrast?application=playwright",
+     "id": "color-contrast",
+     "impact": "serious",
+     "nodes": Array [
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fce7dc",
+               "contrastRatio": 3.15,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#ef4444",
+               "fontSize": "7.5pt (10px)",
+               "fontWeight": "bold",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.15 (foreground color: #ef4444, background color: #fce7dc, font size: 7.5pt (10px), font weight: bold). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600/10 text-red-500 text-[10px] font-black uppercase tracking-widest mb-4\">",
+                 "target": Array [
+                   ".bg-red-600\\/10",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"max-w-[1600px] mx-auto px-6 md:px-10 pb-20 mt-12 bg-[#fffcf0] dark:bg-[#1a1a2e] rounded-[3rem] shadow-xl border border-gray-100 dark:border-white/5 transition-colors duration-500\">",
+                 "target": Array [
+                   ".pb-20",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.15 (foreground color: #ef4444, background color: #fce7dc, font size: 7.5pt (10px), font weight: bold). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600/10 text-red-500 text-[10px] font-black uppercase tracking-widest mb-4\">",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".bg-red-600\\/10",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fffcf0",
+               "contrastRatio": 2.47,
+               "expectedContrastRatio": "3:1",
+               "fgColor": "#a3a2a2",
+               "fontSize": "15.0pt (20px)",
+               "fontWeight": "bold",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 2.47 (foreground color: #a3a2a2, background color: #fffcf0, font size: 15.0pt (20px), font weight: bold). Expected contrast ratio of 3:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"max-w-[1600px] mx-auto px-6 md:px-10 pb-20 mt-12 bg-[#fffcf0] dark:bg-[#1a1a2e] rounded-[3rem] shadow-xl border border-gray-100 dark:border-white/5 transition-colors duration-500\">",
+                 "target": Array [
+                   ".pb-20",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 2.47 (foreground color: #a3a2a2, background color: #fffcf0, font size: 15.0pt (20px), font weight: bold). Expected contrast ratio of 3:1",
+         "html": "<p class=\"text-lg md:text-xl font-bold opacity-40 uppercase tracking-[0.3em] leading-relaxed italic\">Explore the boundaries of generative AI and pure cognition.</p>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-lg",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fffcf0",
+               "contrastRatio": 2.29,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#a6a9ad",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 2.29 (foreground color: #a6a9ad, background color: #fffcf0, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<footer class=\"p-12 text-center text-gray-500 dark:text-gray-400 bg-[#fffcf0] dark:bg-[#1a1a2e] border-t border-black/5 dark:border-white/5 mt-auto transition-colors duration-500\">",
+                 "target": Array [
+                   "footer",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 2.29 (foreground color: #a6a9ad, background color: #fffcf0, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<p class=\"text-xs italic opacity-60\">© 2026 Animetix Team. All rights reserved.</p>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-60.text-xs",
+         ],
+       },
+     ],
+     "tags": Array [
+       "cat.color",
+       "wcag2aa",
+       "wcag143",
+       "TTv5",
+       "TT13.c",
+       "EN-301-549",
+       "EN-9.1.4.3",
+       "ACT",
+       "RGAAv4",
+       "RGAA-3.2.1",
+     ],
+   },
+ ]
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - complementary [ref=e4]:
      - generic [ref=e5]:
        - generic [ref=e7]: MENU
        - button [ref=e8] [cursor=pointer]:
          - img [ref=e9]
      - navigation [ref=e12]:
        - paragraph [ref=e13]: Principal
        - link "Home" [ref=e14] [cursor=pointer]:
          - /url: /static
          - img [ref=e15]
          - text: Home
        - link "Daily Challenge" [ref=e18] [cursor=pointer]:
          - /url: /static/daily-challenge/
          - img [ref=e19]
          - text: Daily Challenge
        - link "Games" [ref=e21] [cursor=pointer]:
          - /url: /static/games/hub/
          - img [ref=e22]
          - text: Games
        - link "Theater" [ref=e24] [cursor=pointer]:
          - /url: /static/theater/
          - img [ref=e25]
          - text: Theater
        - paragraph [ref=e27]: Exploration
        - link "Search" [ref=e28] [cursor=pointer]:
          - /url: /static/search/
          - img [ref=e29]
          - text: Search
        - link "Explore" [ref=e32] [cursor=pointer]:
          - /url: /static/explore/
          - img [ref=e33]
          - text: Explore
        - link "LATENT SPACE" [ref=e36] [cursor=pointer]:
          - /url: /static/lab/latent-space/
          - img [ref=e37]
          - text: LATENT SPACE
        - paragraph [ref=e42]: Community
        - link "Community" [ref=e43] [cursor=pointer]:
          - /url: /static/social/dashboard/
          - img [ref=e44]
          - text: Community
        - link "Leaderboard" [ref=e49] [cursor=pointer]:
          - /url: /static/leaderboard/
          - img [ref=e50]
          - text: Leaderboard
        - paragraph [ref=e56]: Labs & Creation
        - link "Creative Forge" [ref=e57] [cursor=pointer]:
          - /url: /static/lab/forge-hub/
          - img [ref=e58]
          - text: Creative Forge
        - link "Beta Lab" [ref=e61] [cursor=pointer]:
          - /url: /static/lab/
          - img [ref=e62]
          - text: Beta Lab
        - link "Nexus Pro" [ref=e64] [cursor=pointer]:
          - /url: /static/social/nexus/
          - img [ref=e65]
          - text: Nexus Pro
        - link "TRANSPARENCY" [ref=e77] [cursor=pointer]:
          - /url: /static/transparence/
          - img [ref=e78]
          - text: TRANSPARENCY
        - paragraph [ref=e81]: Account
        - link "Connexion" [ref=e82] [cursor=pointer]:
          - /url: /static/auth/login/
          - img [ref=e83]
          - text: Connexion
        - link "S'inscrire" [ref=e86] [cursor=pointer]:
          - /url: /static/auth/register/
          - img [ref=e87]
          - text: S'inscrire
        - generic [ref=e90]:
          - paragraph [ref=e91]: Universes
          - generic [ref=e92]:
            - button "Anime" [ref=e93] [cursor=pointer]
            - button "Manga" [ref=e94] [cursor=pointer]
            - button "Character" [ref=e95] [cursor=pointer]
        - generic [ref=e96]:
          - paragraph [ref=e97]: Difficulty
          - generic [ref=e98]:
            - button "C" [ref=e99] [cursor=pointer]
            - button "B" [ref=e100] [cursor=pointer]
            - button "A" [ref=e101] [cursor=pointer]
            - button "S" [ref=e102] [cursor=pointer]
            - link "P" [ref=e103] [cursor=pointer]:
              - /url: /static/custom-config/
    - complementary [ref=e104]:
      - generic [ref=e105]:
        - generic [ref=e106]: ⚙️ Settings
        - button [ref=e107] [cursor=pointer]:
          - img [ref=e108]
      - generic [ref=e111]:
        - generic [ref=e112]:
          - paragraph [ref=e113]: Appearance
          - generic [ref=e114]:
            - button "Clair" [ref=e115] [cursor=pointer]:
              - img [ref=e116]
              - generic [ref=e122]: Clair
            - button "Sombre" [ref=e123] [cursor=pointer]:
              - img [ref=e124]
              - generic [ref=e126]: Sombre
            - button "Auto" [ref=e127] [cursor=pointer]:
              - img [ref=e128]
              - generic [ref=e130]: Auto
        - generic [ref=e131]:
          - paragraph [ref=e132]: Language
          - generic [ref=e133]:
            - button "Français" [ref=e134] [cursor=pointer]:
              - generic [ref=e135]: Français
              - img [ref=e136]
            - button "English" [ref=e139] [cursor=pointer]:
              - generic [ref=e140]: English
      - paragraph [ref=e142]: Animetix v6.0.4
    - button [ref=e143] [cursor=pointer]:
      - img [ref=e144]
    - navigation [ref=e147]:
      - generic [ref=e148]:
        - button "Toggle Sidebar" [ref=e149] [cursor=pointer]:
          - img [ref=e150]
        - link "Logo" [ref=e151] [cursor=pointer]:
          - /url: /static
          - img "Logo" [ref=e152]
      - generic [ref=e153]:
        - link "Games" [ref=e154] [cursor=pointer]:
          - /url: /static/games/hub/
          - img [ref=e155]
          - text: Games
        - link "Search" [ref=e157] [cursor=pointer]:
          - /url: /static/search/
          - img [ref=e158]
          - text: Search
        - link "Community" [ref=e161] [cursor=pointer]:
          - /url: /static/social/dashboard/
          - img [ref=e162]
          - text: Community
        - link "LATENT SPACE" [ref=e167] [cursor=pointer]:
          - /url: /static/lab/latent-space/
          - img [ref=e168]
          - text: LATENT SPACE
        - link "Creative Forge" [ref=e173] [cursor=pointer]:
          - /url: /static/lab/forge-hub/
          - img [ref=e174]
          - text: Creative Forge
      - generic [ref=e178]:
        - link "Connexion" [ref=e179] [cursor=pointer]:
          - /url: /static/auth/login/
          - img [ref=e180]
          - generic [ref=e183]: Connexion
        - link "S'inscrire" [ref=e184] [cursor=pointer]:
          - /url: /static/auth/register/
          - img [ref=e185]
          - generic [ref=e188]: S'inscrire
    - main [ref=e189]:
      - generic [ref=e191]:
        - generic [ref=e193]:
          - generic [ref=e194]:
            - heading "ANIMETIX" [level=1] [ref=e195]
            - paragraph [ref=e196]: Artificial intelligence in service of your passion.
            - generic [ref=e197]:
              - link "Daily Challenge" [ref=e198] [cursor=pointer]:
                - /url: /static/daily-challenge/
              - link "Leaderboard" [ref=e199] [cursor=pointer]:
                - /url: /static/leaderboard/
          - img "Hero Image" [ref=e201]
        - generic [ref=e202]:
          - generic [ref=e203]:
            - heading "Solo Challenges ." [level=2] [ref=e204]:
              - text: Solo Challenges
              - generic [ref=e205]: .
            - generic [ref=e206]:
              - link "Stars AKINETIX THE SEER The artificial intelligence guesses your favorite anime or manga character. Akinetix" [ref=e208] [cursor=pointer]:
                - /url: /static/akinetix/
                - img "Stars" [ref=e211]
                - generic:
                  - heading "AKINETIX THE SEER" [level=2]:
                    - text: AKINETIX
                    - text: THE SEER
                  - paragraph: The artificial intelligence guesses your favorite anime or manga character.
                - img "Akinetix" [ref=e212]
              - link "Stars CLASSIC THE QUIZ Guess the anime from clues, screenshots, or audio clips. Classic" [ref=e214] [cursor=pointer]:
                - /url: /static/game/classic/
                - img "Stars" [ref=e217]
                - generic:
                  - heading "CLASSIC THE QUIZ" [level=2]:
                    - text: CLASSIC
                    - text: THE QUIZ
                  - paragraph: Guess the anime from clues, screenshots, or audio clips.
                - img "Classic" [ref=e218]
              - link "Stars PARADOX THE ODD ONE Identify the odd one out or temporal paradox generated by the AI. Paradox" [ref=e220] [cursor=pointer]:
                - /url: /static/paradox/
                - img "Stars" [ref=e223]
                - generic:
                  - heading "PARADOX THE ODD ONE" [level=2]:
                    - text: PARADOX
                    - text: THE ODD ONE
                  - paragraph: Identify the odd one out or temporal paradox generated by the AI.
                - img "Paradox" [ref=e224]
              - link "Stars EMOJI QUEST DECODING Decode anime and manga titles hidden behind combinations of emojis. Emoji" [ref=e226] [cursor=pointer]:
                - /url: /static/emoji/
                - img "Stars" [ref=e229]
                - generic:
                  - heading "EMOJI QUEST DECODING" [level=2]:
                    - text: EMOJI QUEST
                    - text: DECODING
                  - paragraph: Decode anime and manga titles hidden behind combinations of emojis.
                - img "Emoji" [ref=e230]
              - link "Stars COVER QUEST THE PUZZLE Rebuild blurry or scrambled manga covers generated by the AI. Covertest" [ref=e232] [cursor=pointer]:
                - /url: /static/covertest/
                - img "Stars" [ref=e235]
                - generic:
                  - heading "COVER QUEST THE PUZZLE" [level=2]:
                    - text: COVER QUEST
                    - text: THE PUZZLE
                  - paragraph: Rebuild blurry or scrambled manga covers generated by the AI.
                - img "Covertest" [ref=e236]
              - link "Stars ANIMINATOR SYNTHESIS The AI generates a customized character. Guess who it is! Animinator" [ref=e238] [cursor=pointer]:
                - /url: /static/animinator/
                - img "Stars" [ref=e241]
                - generic:
                  - heading "ANIMINATOR SYNTHESIS" [level=2]:
                    - text: ANIMINATOR
                    - text: SYNTHESIS
                  - paragraph: The AI generates a customized character. Guess who it is!
                - img "Animinator" [ref=e242]
              - link "Stars ANIME BLINDTEST Recognize legendary OSTs transformed or filtered by AI. Blindtest" [ref=e244] [cursor=pointer]:
                - /url: /static/blindtest/
                - img "Stars" [ref=e247]
                - generic:
                  - heading "ANIME BLINDTEST" [level=2]:
                    - text: ANIME
                    - text: BLINDTEST
                  - paragraph: Recognize legendary OSTs transformed or filtered by AI.
                - img "Blindtest" [ref=e248]
              - link "Stars ARENA ULTIMATUM Trans-dimensional duels moderated by AI. VsBattle" [ref=e250] [cursor=pointer]:
                - /url: /static/game/vsbattle/
                - img "Stars" [ref=e253]
                - generic:
                  - heading "ARENA ULTIMATUM" [level=2]:
                    - text: ARENA
                    - text: ULTIMATUM
                  - paragraph: Trans-dimensional duels moderated by AI.
                - img "VsBattle" [ref=e254]
          - link "EVENT EN COURS WORLD BOSS Join the global community to take down the legendary Titan. World Boss" [ref=e256] [cursor=pointer]:
            - /url: /static/game/world-boss/active/
            - generic [ref=e257]:
              - generic [ref=e260]:
                - generic [ref=e261]: EVENT EN COURS
                - heading "WORLD BOSS" [level=2] [ref=e263]
                - paragraph [ref=e264]: Join the global community to take down the legendary Titan.
              - img "World Boss"
          - generic [ref=e265]:
            - heading "With Friends ." [level=2] [ref=e266]:
              - text: With Friends
              - generic [ref=e267]: .
            - generic [ref=e268]:
              - link "Undercover Unmask the intruder among your friends in a secret word match. Undercover" [ref=e269] [cursor=pointer]:
                - /url: /static/game/duel/lobby/
                - generic [ref=e270]:
                  - heading "Undercover" [level=3] [ref=e271]
                  - paragraph [ref=e272]: Unmask the intruder among your friends in a secret word match.
                - img "Undercover" [ref=e273]
              - link "Code Manga Make your team guess anime/manga cards with the minimum amount of words. Code Manga" [ref=e274] [cursor=pointer]:
                - /url: /static/game/duel/lobby/
                - generic [ref=e275]:
                  - heading "Code Manga" [level=3] [ref=e276]
                  - paragraph [ref=e277]: Make your team guess anime/manga cards with the minimum amount of words.
                - img "Code Manga" [ref=e278]
          - generic [ref=e279]:
            - heading "Creative Forge ." [level=2] [ref=e280]:
              - text: Creative Forge
              - generic [ref=e281]: .
            - link "Fusion CREATIVE FORGE ACCESS THE AI MEDIA LABORATORIES" [ref=e282] [cursor=pointer]:
              - /url: /static/lab/forge-hub/
              - generic [ref=e283]:
                - img "Fusion" [ref=e285]
                - generic [ref=e287]:
                  - heading "CREATIVE FORGE" [level=1] [ref=e288]
                  - paragraph [ref=e289]: ACCESS THE AI MEDIA LABORATORIES
          - generic [ref=e291]:
            - generic [ref=e292]:
              - img [ref=e293]
              - text: NIVEAU OMEGA
            - heading "SINGULARITY LABS" [level=2] [ref=e295]
            - paragraph [ref=e296]: Explore the boundaries of generative AI and pure cognition.
            - link "INITIALISER L'ACCÈS" [ref=e297] [cursor=pointer]:
              - /url: /static/lab/
              - text: INITIALISER L'ACCÈS
              - img [ref=e298]
    - contentinfo [ref=e300]:
      - paragraph [ref=e301]: Powered by Animetix IA & React 19
      - paragraph [ref=e302]: © 2026 Animetix Team. All rights reserved.
    - button "Ask Sensei!" [ref=e303] [cursor=pointer]:
      - img [ref=e304]
      - generic [ref=e306]: Ask Sensei!
  - generic [ref=e307]:
    - img [ref=e309]
    - button "Open Tanstack query devtools" [ref=e357] [cursor=pointer]:
      - img [ref=e358]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import AxeBuilder from '@axe-core/playwright';
  3  | 
  4  | test.describe('Audit d\'Accessibilité (a11y)', () => {
  5  |   // Liste des pages critiques à auditer
  6  |   const pagesToTest = [
  7  |     '/static/',
  8  |     '/static/lab/hub',
  9  |     '/static/explore',
  10 |     '/static/admin',
  11 |     '/static/social/leaderboard'
  12 |   ];
  13 | 
  14 |   for (const route of pagesToTest) {
  15 |     test(`Vérification WCAG sur la route : ${route}`, async ({ page }) => {
  16 |       // Naviguer vers la page
  17 |       await page.goto(route);
  18 |       
  19 |       // Attendre que la page soit complètement chargée (requêtes réseau terminées)
  20 |       await page.waitForLoadState('networkidle');
  21 |       
  22 |       // Lancer l'analyse axe-core
  23 |       const accessibilityScanResults = await new AxeBuilder({ page })
  24 |         .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
  25 |         .analyze();
  26 |       
  27 |       // S'il y a des violations, les afficher dans les logs pour le debug
  28 |       if (accessibilityScanResults.violations.length > 0) {
  29 |         console.error(`Violations trouvées sur ${route}:`);
  30 |         accessibilityScanResults.violations.forEach(v => {
  31 |           console.error(`- Règle: ${v.id} | Impact: ${v.impact} | Description: ${v.description}`);
  32 |           v.nodes.forEach(node => console.error(`   Cible: ${node.target}`));
  33 |         });
  34 |       }
  35 |       
  36 |       // L'attente : aucune violation d'accessibilité ne doit être trouvée
> 37 |       expect(accessibilityScanResults.violations).toEqual([]);
     |                                                   ^ Error: expect(received).toEqual(expected) // deep equality
  38 |     });
  39 |   }
  40 | });
  41 | 
```