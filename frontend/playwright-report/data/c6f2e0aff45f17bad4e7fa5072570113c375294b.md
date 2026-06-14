# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: a11y.spec.ts >> Audit d'Accessibilité (a11y) >> Vérification WCAG sur la route : /static/admin
- Location: e2e\a11y.spec.ts:15:5

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -  1
+ Received  + 58

- Array []
+ Array [
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
+               "bgColor": "#ef4444",
+               "contrastRatio": 3.76,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#ffffff",
+               "fontSize": "12.0pt (16px)",
+               "fontWeight": "bold",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.76 (foreground color: #ffffff, background color: #ef4444, font size: 12.0pt (16px), font weight: bold). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<button class=\"bg-red-500 hover:bg-red-600 text-white font-black py-4 px-8 rounded-full transition-transform hover:scale-105\">REDÉMARRER LE SYSTÈME</button>",
+                 "target": Array [
+                   "button",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.76 (foreground color: #ffffff, background color: #ef4444, font size: 12.0pt (16px), font weight: bold). Expected contrast ratio of 4.5:1",
+         "html": "<button class=\"bg-red-500 hover:bg-red-600 text-white font-black py-4 px-8 rounded-full transition-transform hover:scale-105\">REDÉMARRER LE SYSTÈME</button>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           "button",
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
- generic [ref=e4]:
  - heading "CRITICAL FAILURE" [level=1] [ref=e5]
  - paragraph [ref=e6]: Une erreur inattendue s'est produite lors du rendu de l'interface.
  - generic [ref=e7]: TrendingUp is not defined
  - button "REDÉMARRER LE SYSTÈME" [ref=e8] [cursor=pointer]
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