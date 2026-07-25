import React, { Suspense } from 'react';

// react-plotly.js pulls in plotly.js (~4.6 MB). Load it lazily so the
// plotly-vendor chunk is fetched only when a chart actually mounts, keeping it
// out of each page's critical-path bundle. This also consolidates the CJS/ESM
// default-export shim that was previously duplicated across every plotly page
// (react-plotly.js is declared as an untyped module, hence the casts).
const Plot = React.lazy(async () => {
  const mod = await import('react-plotly.js');
  // react-plotly.js is CJS. Under Vite's *dynamic-import* interop, `mod.default`
  // is the whole `module.exports` object ({ __esModule: true, default: Plot }),
  // not the component — so a naive `mod.default` resolves to [object Object] and
  // React throws "Lazy element type must resolve to a class or function". Unwrap
  // nested `.default` layers until we reach the actual component (a function).
  let candidate: unknown = mod;
  for (let i = 0; i < 5 && candidate && typeof candidate !== 'function'; i += 1) {
    candidate = (candidate as { default?: unknown }).default;
  }
  return { default: candidate as React.ComponentType<Record<string, unknown>> };
});

// Drop-in replacement for the pages' local `Plot` shim. Forwards all props to
// react-plotly.js; the Suspense boundary shows nothing while the chunk loads
// (chart containers own their own sizing, so a null fallback avoids layout
// shift and imposing styles).
export default function LazyPlot(props: Record<string, unknown>) {
  return (
    <Suspense fallback={null}>
      <Plot {...props} />
    </Suspense>
  );
}
