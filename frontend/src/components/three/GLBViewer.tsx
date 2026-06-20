import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

interface GLBViewerProps {
  /** URL of the .glb / .gltf model to display. */
  src: string;
  /** Spin the model automatically (mirrors model-viewer's `auto-rotate`). */
  autoRotate?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Lightweight GLB/GLTF viewer with orbit controls, built on the project's own
 * three.js dependency. Replaces `@google/model-viewer`, which bundled a second
 * copy of three.js for a single usage.
 */
const GLBViewer: React.FC<GLBViewerProps> = ({ src, autoRotate = true, className, style }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 1;
    const height = container.clientHeight || 1;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 3);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // Neutral lighting so PBR materials render without an HDRI environment.
    scene.add(new THREE.AmbientLight(0xffffff, 1.2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2);
    keyLight.position.set(2, 3, 4);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xffffff, 1);
    fillLight.position.set(-3, -1, -2);
    scene.add(fillLight);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 2;

    let model: THREE.Object3D | null = null;
    const loader = new GLTFLoader();
    loader.load(
      src,
      (gltf) => {
        model = gltf.scene;
        // Center the model on the origin and scale it to a consistent size.
        const box = new THREE.Box3().setFromObject(model);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        model.position.sub(center);
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        model.scale.setScalar(2 / maxDim);
        scene.add(model);
      },
      undefined,
      (err) => console.error('GLBViewer: failed to load model', err),
    );

    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const w = container.clientWidth || 1;
      const h = container.clientHeight || 1;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', handleResize);
      controls.dispose();
      renderer.dispose();
      if (model) scene.remove(model);
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [src, autoRotate]);

  return <div ref={containerRef} className={className} style={style} />;
};

export default GLBViewer;
