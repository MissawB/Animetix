/**
 * Typed lazy wrapper for react-force-graph-2d.
 *
 * The library ships a default export whose TypeScript generics confuse
 * React.lazy's type inference, forcing every consumer into an unsafe
 * `as unknown as React.ComponentType<any>` cast (+ the eslint-disable
 * that goes with it).  Centralising the cast here lets the 5 consumer
 * files drop their `any` and the eslint-disable comment.
 *
 * The wrapper also re-exports the type-only imports that consumers need
 * (ForceGraphMethods, NodeObject, LinkObject) so they can import
 * everything from a single module.
 */
import React from 'react';

export type { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d';

// react-force-graph-2d's default export is generic and doesn't play well
// with React.lazy's return-type inference.  The cast is unavoidable (the
// library doesn't expose a named export), so we do it once here instead
// of in every consumer file.
const ForceGraph2D = React.lazy(
  () => import('react-force-graph-2d'),
) as unknown as React.ComponentType<Record<string, unknown>>;

export default ForceGraph2D;
