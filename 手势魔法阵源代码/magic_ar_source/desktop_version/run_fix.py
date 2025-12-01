import http.server
import socketserver
import webbrowser
import os
import sys
import socket

# ---------------------------------------
# 1. 寻找可用端口 (自动避开占用)
# ---------------------------------------
def find_free_port(start_port=8000):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

PORT = find_free_port()

# ---------------------------------------
# 2. 生成修复版 HTML
# ---------------------------------------
html_content = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>Chaos Magic: Scattering Fix</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; font-family: monospace; }
        
        /* 调试面板 */
        #debug-console {
            position: absolute; top: 10px; left: 10px; 
            color: #0f0; background: rgba(0,0,0,0.8); 
            padding: 10px; border: 1px solid #004400; pointer-events: none; z-index: 1000;
            min-width: 200px;
        }
        .log-item { margin-bottom: 4px; }
        .log-ok { color: #0f0; }
        .log-warn { color: #ff0; }
        .log-err { color: #f00; }

        /* 启动层 */
        #overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9); z-index: 999;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            transition: opacity 0.5s;
        }
        h1 { color: #ffaa00; text-shadow: 0 0 20px #ff4400; letter-spacing: 5px; margin-bottom: 30px; font-family: sans-serif; }
        button {
            padding: 15px 50px; background: transparent; border: 2px solid #ffaa00; color: #ffaa00;
            font-size: 18px; cursor: pointer; transition: 0.3s; font-weight: bold;
        }
        button:hover { background: #ffaa00; color: #000; box-shadow: 0 0 30px #ffaa00; }

        #video { position: absolute; top: 0; left: 0; opacity: 0; pointer-events: none; transform: scaleX(-1); }
    </style>
    
    <!-- 核心库 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
</head>
<body>

    <div id="debug-console">
        <div class="log-item">System: Ready</div>
        <div id="log-cam" class="log-item">Camera: Waiting...</div>
        <div id="log-mp" class="log-item">AI Model: Waiting...</div>
        <div id="log-hand" class="log-item">Hand Tracking: ...</div>
    </div>

    <div id="overlay">
        <h1>CHAOS SCATTERING</h1>
        <button onclick="initSystem()">INITIALIZE SYSTEM</button>
    </div>

    <video id="video" playsinline></video>

    <script>
        // 日志工具
        function log(id, msg, type='ok') {
            const el = document.getElementById(id);
            if(el) {
                el.innerText = msg;
                el.className = 'log-item ' + (type=='ok'?'log-ok':(type=='err'?'log-err':'log-warn'));
            }
        }

        let scene, camera, renderer;
        let globalParticles; // 全局粒子系统
        let casters = [];    // 左右手施法者
        let handsModel;
        let isRunning = false;

        // ================= 1. 粒子系统 (Scattering) =================
        class ParticleSystem {
            constructor(scene) {
                this.max = 8000;
                this.idx = 0;
                this.pos = new Float32Array(this.max * 3);
                this.col = new Float32Array(this.max * 3);
                this.vel = new Float32Array(this.max * 3);
                this.life = new Float32Array(this.max);

                const geo = new THREE.BufferGeometry();
                geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
                geo.setAttribute('color', new THREE.BufferAttribute(this.col, 3));

                // 粒子纹理生成
                const cvs = document.createElement('canvas'); cvs.width=32; cvs.height=32;
                const ctx = cvs.getContext('2d');
                const g = ctx.createRadialGradient(16,16,0,16,16,16);
                g.addColorStop(0,'#fff'); g.addColorStop(1,'#000');
                ctx.fillStyle=g; ctx.fillRect(0,0,32,32);
                const tex = new THREE.CanvasTexture(cvs);

                const mat = new THREE.PointsMaterial({
                    size: 0.3, map: tex, vertexColors: true,
                    blending: THREE.AdditiveBlending, depthWrite: false, transparent: true
                });

                this.mesh = new THREE.Points(geo, mat);
                this.mesh.frustumCulled = false; // 防止粒子消失
                scene.add(this.mesh);

                // 初始化隐藏
                for(let i=0; i<this.max*3; i++) this.pos[i] = 99999;
            }

            emit(x, y, z, energy) {
                if(energy < 0.05) return;
                const count = Math.floor(2 + energy * 10);
                
                for(let k=0; k<count; k++) {
                    const i = this.idx; 
                    const i3 = i*3;
                    
                    // 位置：手心周围
                    const r = 2.0 * Math.random() * (0.5 + energy); 
                    const a = Math.random() * 6.28;
                    this.pos[i3] = x + Math.cos(a)*r;
                    this.pos[i3+1] = y + Math.sin(a)*r;
                    this.pos[i3+2] = z + (Math.random()-0.5);

                    // 速度：向上漂浮 + 扩散
                    const spd = 0.1 + energy * 0.2;
                    this.vel[i3] = (Math.random()-0.5) * spd;
                    this.vel[i3+1] = Math.random() * spd * 0.5 + 0.05; // 向上
                    this.vel[i3+2] = (Math.random()-0.5) * spd;

                    // 颜色 (R, G, B)
                    this.life[i] = 1.0;
                    this.col[i3] = 1.0;   // R
                    this.col[i3+1] = 0.8; // G
                    this.col[i3+2] = 0.2; // B
                    
                    this.idx = (this.idx + 1) % this.max;
                }
            }

            update() {
                for(let i=0; i<this.max; i++) {
                    if(this.life[i] > 0) {
                        const i3 = i*3;
                        // 物理
                        this.pos[i3] += this.vel[i3];
                        this.pos[i3+1] += this.vel[i3+1];
                        this.pos[i3+2] += this.vel[i3+2];
                        
                        // 重力 & 阻力
                        this.vel[i3+1] -= 0.005; // 重力下坠
                        this.vel[i3] *= 0.98;
                        this.vel[i3+1] *= 0.98;
                        this.vel[i3+2] *= 0.98;

                        // 衰减
                        this.life[i] -= 0.015;
                        const l = this.life[i];

                        // 变色：白 -> 黄 -> 红 -> 黑
                        this.col[i3] = l; 
                        this.col[i3+1] = l * l * 0.5; 
                        this.col[i3+2] = 0;
                        
                        if(l<=0) this.pos[i3] = 99999;
                    }
                }
                this.mesh.geometry.attributes.position.needsUpdate = true;
                this.mesh.geometry.attributes.color.needsUpdate = true;
            }
        }

        // ================= 2. 魔法阵 =================
        class Caster {
            constructor(scene) {
                this.mesh = new THREE.Group();
                this.energy = 0;
                this.targetEnergy = 0;
                
                // 简单的环
                const mat = new THREE.LineBasicMaterial({color: 0xffaa00, transparent: true, opacity: 0.5});
                // 为了简单不报错，这里用点云模拟环
                const pMat = new THREE.PointsMaterial({size: 0.15, color: 0xffaa00, blending: THREE.AdditiveBlending, transparent: true});
                
                this.rings = [];
                [5, 3.5, 2].forEach((r, idx) => {
                   const pts = [];
                   for(let i=0; i<50; i++) {
                       const a = (i/50)*6.28;
                       pts.push(Math.cos(a)*r, Math.sin(a)*r, 0);
                   }
                   const geo = new THREE.BufferGeometry();
                   geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
                   const p = new THREE.Points(geo, pMat);
                   p.userData = { speed: (idx%2==0?1:-1)*0.02 };
                   this.rings.push(p);
                   this.mesh.add(p);
                });

                scene.add(this.mesh);
                this.mesh.visible = false;
            }

            update(hand) {
                if(hand) {
                    this.mesh.visible = true;
                    this.mesh.position.lerp(new THREE.Vector3(hand.x, hand.y, 0), 0.3);
                    this.targetEnergy = hand.pinch;
                } else {
                    this.targetEnergy = 0;
                    if(this.energy < 0.05) this.mesh.visible = false;
                }

                this.energy += (this.targetEnergy - this.energy) * 0.1;
                
                // 环动画
                this.rings.forEach(r => {
                    r.rotation.z += r.userData.speed * (1 + this.energy * 5);
                    r.material.opacity = 0.3 + this.energy * 0.7;
                });

                // ★ 发射粒子 ★
                if(this.mesh.visible && this.energy > 0.1) {
                    const p = this.mesh.position;
                    globalParticles.emit(p.x, p.y, p.z, this.energy);
                }
            }
        }

        // ================= 3. 系统初始化 =================
        async function initSystem() {
            // 隐藏 UI
            document.getElementById('overlay').style.opacity = 0;
            setTimeout(() => document.getElementById('overlay').style.display = 'none', 500);

            // 1. Three.js
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 100);
            camera.position.z = 20;
            renderer = new THREE.WebGLRenderer({antialias:true});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            globalParticles = new ParticleSystem(scene);
            casters = [new Caster(scene), new Caster(scene)];

            log('log-mp', 'Loading Model...');

            // 2. MediaPipe
            const video = document.getElementById('video');
            handsModel = new Hands({locateFile: (file) => {
                return "https://cdn.jsdelivr.net/npm/@mediapipe/hands/" + file;
            }});
            
            handsModel.setOptions({
                maxNumHands: 2,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            handsModel.onResults(onResults);

            log('log-cam', 'Starting Camera...');
            const cam = new Camera(video, {
                onFrame: async () => { await handsModel.send({image: video}); },
                width: 640, height: 480
            });
            
            try {
                await cam.start();
                log('log-cam', 'Camera Active ✅');
                log('log-mp', 'Model Loaded ✅');
                isRunning = true;
                animate();
            } catch(e) {
                log('log-cam', 'Error: ' + e, 'err');
            }
        }

        function onResults(results) {
            const handData = [null, null];
            if(results.multiHandLandmarks) {
                log('log-hand', 'Hands Detected: ' + results.multiHandLandmarks.length, 'ok');
                results.multiHandLandmarks.forEach((lm, i) => {
                    if(i < 2) {
                        // 简单的坐标映射
                        const vFOV = THREE.Math.degToRad(60);
                        const height = 2 * Math.tan(vFOV / 2) * 20;
                        const width = height * (window.innerWidth/window.innerHeight);
                        
                        // 镜像修正
                        const x = -(lm[9].x - 0.5) * width;
                        const y = -(lm[9].y - 0.5) * height;
                        
                        const dist = Math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y);
                        let energy = (dist - 0.03) / 0.2;
                        energy = Math.max(0, Math.min(1, energy));
                        
                        handData[i] = {x, y, pinch: energy};
                    }
                });
            } else {
                log('log-hand', 'No Hands', 'warn');
            }
            window.currentHands = handData;
        }

        function animate() {
            if(!isRunning) return;
            requestAnimationFrame(animate);
            
            const hands = window.currentHands || [null, null];

            // 更新粒子系统
            globalParticles.update();

            // 更新左右手
            casters[0].update(hands[0]);
            casters[1].update(hands[1]);

            renderer.render(scene, camera);
        }

        window.onresize = () => {
            camera.aspect = window.innerWidth/window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ System fixed.")
print(f"✅ Running on port: {PORT} (Auto-selected)")
print(f"👉 Open: http://localhost:{PORT}")

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Server active. Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
