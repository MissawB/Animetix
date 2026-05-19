/**
 * Latent Space 3D Visualization
 */

function toggleInfo() {
    const panel = document.getElementById('info-panel');
    const icon = document.getElementById('info-icon');
    if (!panel || !icon) return;
    panel.classList.toggle('collapsed');
    if (panel.classList.contains('collapsed')) {
        icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
    } else {
        icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
    }
}

window.toggleInfo = toggleInfo;

document.addEventListener('DOMContentLoaded', function() {
    const dataElement = document.getElementById('latent-data');
    if (!dataElement) return;

    const config = JSON.parse(dataElement.textContent);
    const rawData = config.rawData;
    const frierenImgUrl = config.frierenImgUrl;
    const loader = document.getElementById('loader');

    if (!rawData || rawData.length === 0) {
        const plotContainer = document.getElementById('latent-plot');
        if (plotContainer) {
            plotContainer.innerHTML = `
                <div class="flex h-full items-center justify-center text-white/20">
                    <div class="text-center">
                        <i class="bi bi-broadcast text-6xl mb-4 block animate-pulse"></i>
                        <p class="uppercase font-bold tracking-[0.3em] text-xs">Signal Lost: No Data</p>
                    </div>
                </div>`;
        }
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.style.display = 'none', 700);
        }
        return;
    }

    // Stats updates
    const statPoints = document.getElementById('stat-points');
    if (statPoints) statPoints.innerText = rawData.length;
    
    // --- THREE.JS SETUP ---
    const container = document.getElementById('latent-plot');
    if (!container) return;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.02);

    const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(10, 10, 15);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;

    // Colors mapping
    const genreColors = {
        'Action': 0xff4b4b,
        'Adventure': 0xf59e0b,
        'Comedy': 0xfffc00,
        'Drama': 0x8b5cf6,
        'Fantasy': 0x10b981,
        'Romance': 0xec4899,
        'Sci-Fi': 0x00f2ff,
        'Horror': 0x7f1d1d,
        'Mystery': 0x1e40af,
        'Slice of Life': 0x93c5fd,
        'Psychological': 0x4c1d95,
        'Supernatural': 0x059669,
        'Sports': 0xfbbf24,
        'Mecha': 0x3b82f6,
        'Music': 0xf472b6
    };

    const defaultPalette = [
        0x00f2ff, 0x10b981, 0xf59e0b, 0x8b5cf6, 
        0xec4899, 0xfffc00, 0x76ff03, 0xf97316, 0x00e5ff,
        0xd500f9, 0x00b0ff, 0xff1744, 0xffea00, 0x00e676
    ];

    // Create particles
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(rawData.length * 3);
    const colors = new Float32Array(rawData.length * 3);
    const userData = []; // Store metadata for raycasting

    let uniqueCategories = new Set();

    rawData.forEach((p, i) => {
        // Position
        positions[i * 3] = p.x * 5;
        positions[i * 3 + 1] = p.y * 5;
        positions[i * 3 + 2] = p.z * 5;

        // Color
        const cat = p.category || p.genre || "Inconnu";
        uniqueCategories.add(cat);
        
        let colorHex = genreColors[cat];
        if (!colorHex) {
            let hash = 0;
            for (let j = 0; j < cat.length; j++) {
                hash = cat.charCodeAt(j) + ((hash << 5) - hash);
            }
            colorHex = defaultPalette[Math.abs(hash) % defaultPalette.length];
        }
        
        const color = new THREE.Color(colorHex);
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;

        userData.push(p);
    });

    const statClusters = document.getElementById('stat-clusters');
    if (statClusters) statClusters.innerText = uniqueCategories.size;

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.15,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true
    });

    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    const raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 0.2;
    const mouse = new THREE.Vector2();

    container.addEventListener('click', onClick, false);

    function onClick(event) {
        const rect = container.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObject(particleSystem);

        if (intersects.length > 0) {
            const index = intersects[0].index;
            const entity = userData[index];
            
            showEntityIntel(entity);
            
            const targetPos = new THREE.Vector3(
                positions[index * 3],
                positions[index * 3 + 1],
                positions[index * 3 + 2]
            );
            
            const offset = new THREE.Vector3(1, 1, 1).normalize().multiplyScalar(3);
            const camPos = targetPos.clone().add(offset);
            
            // Simple animation
            camera.position.lerp(camPos, 0.1);
            controls.target.copy(targetPos);
        }
    }

    function showEntityIntel(entity) {
        const titleEl = document.getElementById('intel-title');
        const catEl = document.getElementById('intel-cat');
        const yearEl = document.getElementById('intel-year');
        const imgEl = document.getElementById('intel-img');

        if (titleEl) titleEl.innerText = entity.title;
        if (catEl) catEl.innerText = entity.category || entity.genre || 'N/A';
        if (yearEl) yearEl.innerText = entity.year || '????';
        if (imgEl) imgEl.src = entity.image || frierenImgUrl;
        
        const defaultHeader = document.getElementById('default-header');
        const defaultInfo = document.getElementById('default-info');
        const intelPanel = document.getElementById('entity-intel');

        if (defaultHeader) defaultHeader.classList.add('hidden');
        if (defaultInfo) defaultInfo.classList.add('hidden');
        if (intelPanel) {
            intelPanel.classList.remove('hidden');
            intelPanel.style.opacity = '0';
            setTimeout(() => { intelPanel.style.opacity = '1'; }, 50);
        }
    }

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    
    animate();

    window.addEventListener('resize', onWindowResize, false);
    function onWindowResize() {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }

    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.style.display = 'none', 700);
    }
});
