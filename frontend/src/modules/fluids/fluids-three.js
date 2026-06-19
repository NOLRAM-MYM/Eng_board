/**
 * frontend/src/modules/fluids/fluids-three.js
 * ===============================================
 * Three.js 3D pipe flow simulation.
 *
 * Scene composition:
 *   - Transparent cylindrical pipe (along X axis)
 *   - 600 coloured particles with velocity-dependent speed
 *   - Velocity-to-colour mapping: blue (slow) → green → red (fast)
 *   - Parabolic profile for laminar, power-law for turbulent
 *   - Slow camera orbit for depth
 *
 * Exports:
 *   ThreePipe.init(canvasId)
 *   ThreePipe.updateParticles(result)
 */

import * as THREE from 'three';

export const ThreePipe = {
  scene:      null,
  camera:     null,
  renderer:   null,
  particles:  null,
  animating:  true,
  velocities: [],
  clock:      null,

  // ---------------------------------------------------------------
  // init(canvasId)
  // ---------------------------------------------------------------
  init(canvasId = 'three-canvas') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) { console.warn('[ThreePipe] Canvas not found:', canvasId); return; }

    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x050b18);

    // Camera
    const w = canvas.offsetWidth || 300;
    const h = canvas.offsetHeight || 280;
    this.camera = new THREE.PerspectiveCamera(48, w / h, 0.01, 100);
    this.camera.position.set(3.5, 1.8, 3.5);
    this.camera.lookAt(0, 0, 0);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(w, h);

    // Clock (for time-based animation)
    this.clock = new THREE.Clock();

    // Lighting
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const dir = new THREE.DirectionalLight(0x6699ff, 1.4);
    dir.position.set(3, 5, 4);
    this.scene.add(dir);

    // Build static pipe geometry
    this._buildPipe();

    // Default particles (before first calculation)
    this.createParticles(1.0, 'Laminar');

    // Animation loop
    this._animate();

    // Toggle button
    const toggleBtn = document.getElementById('toggle-animation');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        this.animating = !this.animating;
        toggleBtn.textContent = this.animating ? '⏸ Pause' : '▶ Resume';
        if (this.animating) this._animate();
      });
    }

    // Responsive resize
    const resizeObs = new ResizeObserver(() => this._onResize(canvasId));
    resizeObs.observe(canvas);
  },

  // ---------------------------------------------------------------
  // _buildPipe()
  // ---------------------------------------------------------------
  _buildPipe() {
    const PIPE_R = 0.5;
    const PIPE_L = 4.0;

    // Transparent pipe shell
    const shellGeo = new THREE.CylinderGeometry(PIPE_R, PIPE_R, PIPE_L, 48, 1, true);
    const shellMat = new THREE.MeshPhongMaterial({
      color:       0x1e3a5f,
      transparent: true,
      opacity:     0.22,
      side:        THREE.DoubleSide,
    });
    const shell = new THREE.Mesh(shellGeo, shellMat);
    shell.rotation.z = Math.PI / 2;
    this.scene.add(shell);

    // Wireframe overlay for tech aesthetic
    const wireMat = new THREE.MeshBasicMaterial({
      color:       0x3b82f6,
      wireframe:   true,
      transparent: true,
      opacity:     0.06,
    });
    const wire = new THREE.Mesh(shellGeo, wireMat);
    wire.rotation.z = Math.PI / 2;
    this.scene.add(wire);

    // End caps (glowing rings)
    const ringGeo = new THREE.TorusGeometry(PIPE_R, 0.018, 12, 48);
    const ringMat = new THREE.MeshPhongMaterial({
      color:       0x3b82f6,
      emissive:    new THREE.Color(0x1e40af),
      transparent: true,
      opacity:     0.7,
    });
    [-PIPE_L / 2, PIPE_L / 2].forEach(x => {
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.x = x;
      ring.rotation.y = Math.PI / 2;
      this.scene.add(ring);
    });

    // Centre-line dashed indicator
    const lineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-PIPE_L / 2, 0, 0),
      new THREE.Vector3(PIPE_L / 2,  0, 0),
    ]);
    const lineMat = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.2 });
    this.scene.add(new THREE.Line(lineGeo, lineMat));
  },

  // ---------------------------------------------------------------
  // createParticles(maxVelocity, regime)
  // ---------------------------------------------------------------
  createParticles(maxVelocity, regime) {
    if (this.particles) {
      this.scene.remove(this.particles);
      this.particles.geometry.dispose();
      this.particles.material.dispose();
    }

    const N     = 800;
    const R     = 0.46;   // Slightly less than pipe radius (scene units)
    const L     = 4.0;

    const positions = new Float32Array(N * 3);
    const colors    = new Float32Array(N * 3);
    this.velocities = new Array(N);

    for (let i = 0; i < N; i++) {
      // Uniform random distribution in cylinder cross-section
      const rNorm = Math.sqrt(Math.random());   // r/R ∈ [0,1], area-weighted
      const theta = Math.random() * Math.PI * 2;
      const r     = rNorm * R;
      const x     = (Math.random() - 0.5) * L; // Random start along pipe

      positions[i * 3]     = x;
      positions[i * 3 + 1] = r * Math.cos(theta);
      positions[i * 3 + 2] = r * Math.sin(theta);

      // Velocity profile (normalised 0–1)
      let vNorm;
      if (regime === 'Laminar') {
        // Exact parabolic: v/v_max = 1 - (r/R)²
        vNorm = 1.0 - rNorm * rNorm;
      } else {
        // 1/7th power law: v/v_max ≈ (1 - r/R)^(1/7)
        vNorm = Math.pow(Math.max(0, 1 - rNorm), 1 / 7);
      }

      // Actual speed for animation (scene units per frame)
      this.velocities[i] = vNorm * maxVelocity;

      // HSL colour: hue 240° (blue, slow) → 0° (red, fast)
      const hue  = (1 - vNorm) * 240 / 360;  // 0.667 (blue) → 0 (red)
      const col  = new THREE.Color().setHSL(hue, 1.0, 0.55);
      colors[i * 3]     = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colors,    3));

    const mat = new THREE.PointsMaterial({
      size:          0.032,
      vertexColors:  true,
      transparent:   true,
      opacity:       0.88,
      sizeAttenuation: true,
    });

    this.particles = new THREE.Points(geo, mat);
    this.scene.add(this.particles);
  },

  // ---------------------------------------------------------------
  // updateParticles(result)  — called after each calculation
  // ---------------------------------------------------------------
  updateParticles(result) {
    if (!this.scene) return;
    const maxV = Math.max(result.velocity_m_s, 0.01);
    this.createParticles(maxV, result.flow_regime);
  },

  // ---------------------------------------------------------------
  // _animate() — RAF loop
  // ---------------------------------------------------------------
  _animate() {
    if (!this.animating) return;
    requestAnimationFrame(() => this._animate());

    const dt = Math.min(this.clock?.getDelta() ?? 0.016, 0.05);

    if (this.particles) {
      const pos  = this.particles.geometry.attributes.position;
      const HALF = 2.0;  // half pipe length

      for (let i = 0; i < pos.count; i++) {
        // Advance along pipe (X axis)
        pos.array[i * 3] += this.velocities[i] * dt * 0.8;

        // Wrap around
        if (pos.array[i * 3] > HALF) {
          pos.array[i * 3] = -HALF;
        }
      }
      pos.needsUpdate = true;
    }

    // Slow camera orbit for depth perception
    if (this.camera && this.clock) {
      const t = this.clock.elapsedTime * 0.12;
      const R = 5.5;
      this.camera.position.x = Math.sin(t) * R * 0.6;
      this.camera.position.z = Math.cos(t) * R;
      this.camera.position.y = 1.8;
      this.camera.lookAt(0, 0, 0);
    }

    this.renderer?.render(this.scene, this.camera);
  },

  // ---------------------------------------------------------------
  // _onResize(canvasId)
  // ---------------------------------------------------------------
  _onResize(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !this.renderer) return;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    if (w === 0 || h === 0) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  },
};
