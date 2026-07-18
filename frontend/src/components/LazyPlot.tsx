import React, { Suspense } from 'react';

// react-plotly.js pulls in plotly.js (~4.6 MB). Load it lazily so the
// plotly-vendor chunk is fetched only when a chart actually mounts, keeping it
// out of each page's critical-path bundle. This also consolidates the CJS/ESM
// default-export shim that was previously duplicated across every plotly page
// (react-plotly.js is declared as an untyped module, hence the casts).
const Plot = React.lazy(async () => {
  const mod = await import('react-plotly.js');
  const Component =
    (mod as unknown as { default?: React.ComponentType<Record<string, unknown>> }).default ??
    (mod as unknown as React.ComponentType<Record<string, unknown>>);
  return { default: Component };
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
