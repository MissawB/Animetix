/**
 * Spatial Lab - 3D Reconstruction Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('spatial-data');
    if (!dataElement) return;

    const config = JSON.parse(dataElement.textContent);
    const generateDepthUrl = config.generateDepthUrl;
    const csrfToken = config.csrfToken;

    let scene, camera, renderer, plane, material;
    let targetRotationX = 0, targetRotationY = 0;
    let currentRotationX = 0, currentRotationY = 0;
    let activeIntervals = [];

    function init3D() {
        const container = document.getElementById('webgl-container');
        if (!container) return;
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.z = 5;
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);
        
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        container.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            targetRotationY = ((e.clientX - rect.left) / rect.width - 0.5) * 0.4;
            targetRotationX = ((e.clientY - rect.top) / rect.height - 0.5) * 0.4;
        });
        animate();
    }

    function createSpatialPlane(imageUrl, depthMapUrl) {
        const loader = new THREE.TextureLoader();
        loader.load(imageUrl, (texture) => {
            loader.load(depthMapUrl, (depthMap) => {
                if (plane) scene.remove(plane);
                const aspect = texture.image.width / texture.image.height;
                const geometry = new THREE.PlaneGeometry(4 * aspect, 4, 512, 512);

                material = new THREE.ShaderMaterial({
                    uniforms: { 
                        uTexture: { value: texture }, 
                        uDepthMap: { value: depthMap }, 
                        uStrength: { value: 0.35 }, 
                        uZoom: { value: 1.0 }
                    },
                    vertexShader: `
                        varying vec2 vUv;
                        uniform sampler2D uDepthMap;
                        uniform float uStrength;
                        uniform float uZoom;

                        void main() {
                            vUv = uv;
                            vec4 depthSample = texture2D(uDepthMap, uv);
                            float d = (depthSample.r + depthSample.g + depthSample.b) / 3.0;
                            
                            vec3 newPos = position;
                            newPos.z += d * uStrength;
                            
                            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos * uZoom, 1.0);
                        }
                    `,
                    fragmentShader: `
                        varying vec2 vUv;
                        uniform sampler2D uTexture;

                        void main() {
                            gl_FragColor = texture2D(uTexture, vUv);
                        }
                    `,
                    side: THREE.DoubleSide
                });
                plane = new THREE.Mesh(geometry, material);
                scene.add(plane);
                const overlay = document.getElementById('loading-overlay');
                if (overlay) overlay.classList.add('d-none');
                if (window.sounds) window.sounds.play('reveal');
            });
        });
    }

    function animate() {
        requestAnimationFrame(animate);
        if (plane) {
            currentRotationX += (targetRotationX - currentRotationX) * 0.05;
            currentRotationY += (targetRotationY - currentRotationY) * 0.05;
            plane.rotation.x = currentRotationX; plane.rotation.y = currentRotationY;
            if (material) {
                const strengthInput = document.getElementById('depth-strength');
                const zoomInput = document.getElementById('depth-zoom');
                if (strengthInput) material.uniforms.uStrength.value = strengthInput.value / 100 * 0.8;
                if (zoomInput) material.uniforms.uZoom.value = zoomInput.value / 100;
            }
        }
        if (renderer && scene && camera) renderer.render(scene, camera);
    }

    function loadFromUrl() {
        const input = document.getElementById('url-input');
        const url = input ? input.value.trim() : '';
        if (url) selectImage(url, "URL Image");
    }

    function uploadImage(input) {
        if (input.files && input.files[0]) {
            const file = input.files[0];
            selectImage(null, file.name, file);
        }
    }

    function selectImage(url, title, file = null) {
        const overlay = document.getElementById('loading-overlay');
        const progressBar = document.getElementById('progress-bar');
        const statusLabel = document.getElementById('status-label');
        const progressPercent = document.getElementById('progress-percent');
        const timeLabel = document.getElementById('estimated-time');
        const renderTitle = document.getElementById('render-title');
        
        if (overlay) overlay.classList.remove('d-none');
        if (renderTitle) renderTitle.innerText = title;
        
        // Reset UI
        activeIntervals.forEach(clearInterval); activeIntervals = [];
        let progress = 0; let secondsPassed = 0;
        if (progressBar) progressBar.style.width = '0%';
        if (progressPercent) progressPercent.innerText = '0%';
        if (timeLabel) timeLabel.innerText = "Calcul en cours...";

        // Timer
        const globalTimer = setInterval(() => {
            secondsPassed++;
            if (timeLabel) timeLabel.innerText = `Temps écoulé : ${secondsPassed}s`;
            const patienceMsg = document.getElementById('patience-msg');
            if (secondsPassed > 20 && patienceMsg) patienceMsg.innerText = "Presque fini... L'IA optimise le maillage 3D.";
        }, 1000);
        activeIntervals.push(globalTimer);

        // Progress simulation
        const progressTimer = setInterval(() => {
            if (progress < 90) {
                progress += (progress < 40 ? 1 : 0.2);
                if (progressBar) progressBar.style.width = progress + '%';
                if (progressPercent) progressPercent.innerText = Math.floor(progress) + '%';
            }
            if (statusLabel) {
                if (progress < 25) statusLabel.innerText = file ? "📤 Téléversement..." : "📥 Téléchargement...";
                else if (progress < 60) statusLabel.innerText = "🧠 Inférence Neuronale...";
                else statusLabel.innerText = "🏗️ Reconstruction 3D...";
            }
        }, 100);
        activeIntervals.push(progressTimer);

        const formData = new FormData();
        if (file) formData.append('image_file', file);
        else formData.append('image_url', url);
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch(generateDepthUrl, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                progress = 100;
                if (progressBar) progressBar.style.width = '100%';
                if (progressPercent) progressPercent.innerText = '100%';
                if (statusLabel) statusLabel.innerText = "✅ Géométrie prête !";
                setTimeout(() => createSpatialPlane(data.original_image_b64, data.depth_map), 200);
            } else {
                throw new Error(data.error);
            }
        })
        .catch(err => {
            console.error("Spatial Error:", err);
            alert("Erreur: " + err.message);
            if (overlay) overlay.classList.add('d-none');
        })
        .finally(() => {
            activeIntervals.forEach(clearInterval);
        });
    }

    function resetCamera() { 
        targetRotationX = 0; targetRotationY = 0; 
        const strengthInput = document.getElementById('depth-strength');
        const zoomInput = document.getElementById('depth-zoom');
        if (strengthInput) strengthInput.value = 50;
        if (zoomInput) zoomInput.value = 100;
    }

    // Expose to window
    window.loadFromUrl = loadFromUrl;
    window.uploadImage = uploadImage;
    window.selectImage = selectImage;
    window.resetCamera = resetCamera;

    init3D();
});
