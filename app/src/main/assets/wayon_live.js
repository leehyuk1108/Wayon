(() => {
    "use strict";

    const HEADER_SIZE = 24;
    const MAX_PAYLOAD_SIZE = 4 * 1024 * 1024;
    const FRAME_METADATA = 0;
    const FRAME_WIDE = 1;
    const FRAME_DRIVER = 2;
    const FRAME_STATUS = 3;
    const FLAG_KEY = 1;
    const DEG = Math.PI / 180;
    const COLOR_SAMPLE_INTERVAL_MS = 1500;
    const WIDE_EXPOSURE_SAMPLE_INTERVAL_MS = 250;
    const WIDE_EXPOSURE_TARGET_LUMA = 24;
    const WIDE_EXPOSURE_MAX_GAIN = 1.55;
    const WIDE_EXPOSURE_HOLD_MS = 4000;
    const WIDE_EXPOSURE_FADE_MS = 2000;
    const WIDE_READY_P90_LUMA = 30;
    const WIDE_READY_TIMEOUT_MS = 3000;
    const DRIVER_BLEND_HOLD_MS = 1000;
    const DRIVER_BLEND_RAMP_MS = 3500;
    const FRAME_SYNC_TOLERANCE_US = 100_000;
    const SINGLE_CAMERA_STARTUP_MS = 250;
    const CONTROL_MAGIC = [87, 76, 67, 49];
    const CONTROL_PHOTO = 1;
    const CONTROL_CLIP = 2;

    const overlay = document.getElementById("wayon-live-overlay");
    const canvas = document.getElementById("wayon-live-canvas");
    const status = document.getElementById("wayon-live-status");
    const statusText = document.getElementById("wayon-live-status-text");
    const compass = document.getElementById("wayon-live-compass");
    const message = document.getElementById("wayon-live-message");
    const messageText = document.getElementById("wayon-live-message-text");
    const spinner = document.getElementById("wayon-live-spinner");
    const retry = document.getElementById("btnWayonLiveRetry");
    const impactPanel = document.getElementById("wayon-live-impact-panel");
    const impactTime = document.getElementById("wayon-live-impact-time");
    const impactForce = document.getElementById("wayon-live-impact-force");
    const impactLocation = document.getElementById("wayon-live-impact-location");
    const impactLock = document.getElementById("wayon-live-impact-lock");
    const saveToast = document.getElementById("wayon-live-save-toast");
    const photoButton = document.getElementById("btnWayonLivePhoto");
    const clip10Button = document.getElementById("btnWayonLiveClip10");
    const clip30Button = document.getElementById("btnWayonLiveClip30");
    const playbackBar = document.getElementById("wayon-live-playback-bar");
    const playbackToggle = document.getElementById("btnWayonLivePlaybackToggle");
    const playbackProgress = document.getElementById("wayon-live-playback-progress");
    const playbackTime = document.getElementById("wayon-live-playback-time");

    let socket = null;
    let intentionalClose = false;
    let terminalState = null;
    let reconnectAttempts = 0;
    let reconnectTimer = 0;
    let sessionRequestPending = false;
    let startupTimer = 0;
    let heartbeatTimer = 0;
    let nativeRefreshSuspended = false;
    let impactRequestSequence = 0;
    let saveToastTimer = 0;
    let photoCaptureBusy = false;
    let receiveBuffer = new Uint8Array(0);
    let metadata = null;
    let glState = null;
    let animationFrame = 0;
    let yaw = 0;
    let pitch = 0;
    let viewFov = 78 * DEG;
    let yawVelocity = 0;
    let pitchVelocity = 0;
    let lastRenderAt = 0;
    let frameCounter = 0;
    let measuredFps = 0;
    let fpsStartedAt = 0;
    let colorSampleCanvas = null;
    let colorSampleContext = null;
    const nextColorSampleAt = { wide: 0, driver: 0 };
    const edgeColorSamples = { wide: null, driver: null };
    let driverColorGain = [1, 1, 1];
    let nextWideExposureSampleAt = 0;
    let wideFirstFrameAt = 0;
    let driverFirstFrameAt = 0;
    let wideExposureSamples = 0;
    let wideMeasuredExposureGain = 1;
    let wideExposureReady = false;
    const pointers = new Map();
    let pinchStart = null;
    let savedPlayback = null;
    let savedPlaybackRequest = null;
    let savedLoadSequence = 0;
    const MAX_DECODE_QUEUE = 12;
    const MAX_RECONNECT_ATTEMPTS = 6;

    const streams = {
        wide: {
            decoder: null, frame: null, frameReceivedAt: 0, ready: false,
            keySeen: false, droppingUntilKey: false, lastTimestamp: -1,
        },
        driver: {
            decoder: null, frame: null, frameReceivedAt: 0, ready: false,
            keySeen: false, droppingUntilKey: false, lastTimestamp: -1,
        },
    };

    const vertexShader = `
        attribute vec2 aPosition;
        varying vec2 vUv;
        void main() {
            vUv = aPosition * 0.5 + 0.5;
            gl_Position = vec4(aPosition, 0.0, 1.0);
        }
    `;

    const fragmentShader = `
        precision highp float;
        varying vec2 vUv;
        uniform sampler2D uWide;
        uniform sampler2D uDriver;
        uniform float uYaw;
        uniform float uPitch;
        uniform float uViewFov;
        uniform float uAspect;
        uniform float uProjectionMode;
        uniform float uWideYaw;
        uniform float uDriverYaw;
        uniform float uWidePitch;
        uniform float uDriverPitch;
        uniform float uWideRoll;
        uniform float uDriverRoll;
        uniform vec2 uWideFocalScale;
        uniform vec2 uDriverFocalScale;
        uniform float uWideMaxTheta;
        uniform float uDriverMaxTheta;
        uniform float uWideMaxThetaBias;
        uniform float uDriverMaxThetaBias;
        uniform vec3 uWidePosition;
        uniform vec3 uDriverPosition;
        uniform float uSphereRadius;
        uniform float uBlend;
        uniform float uDriverMirror;
        uniform float uWideReady;
        uniform float uDriverReady;
        uniform vec2 uWideFisheyeDistortion;
        uniform vec2 uDriverFisheyeDistortion;
        uniform vec2 uWideOpticalCenter;
        uniform vec2 uDriverOpticalCenter;
        uniform float uWideExposureGain;
        uniform float uDriverBlendReadiness;
        uniform vec3 uDriverColorGain;
        uniform float uWideVignette;
        uniform float uDriverVignette;

        const float PI = 3.141592653589793;

        float wrapPi(float angle) {
            return mod(angle + PI, 2.0 * PI) - PI;
        }

        float inBounds(vec2 uv) {
            return step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
        }

        vec3 directionFromYawPitch(float directionYaw, float directionPitch) {
            float cosPitch = cos(directionPitch);
            return vec3(
                sin(directionYaw) * cosPitch,
                sin(directionPitch),
                cos(directionYaw) * cosPitch
            );
        }

        vec3 viewDirection() {
            if (uProjectionMode > 0.5) {
                float worldYaw = wrapPi(uYaw + (vUv.x - 0.5) * uViewFov);
                float worldPitch = uPitch + (vUv.y - 0.5) * (uViewFov / uAspect);
                return directionFromYawPitch(worldYaw, worldPitch);
            }

            vec2 screen = vUv * 2.0 - 1.0;
            float tanHalfVertical = tan(min(uViewFov, PI - 0.001) * 0.5);
            float tanHalfHorizontal = tanHalfVertical * max(uAspect, 0.001);
            vec3 forward = directionFromYawPitch(uYaw, uPitch);
            vec3 right = normalize(vec3(cos(uYaw), 0.0, -sin(uYaw)));
            vec3 up = normalize(cross(forward, right));
            return normalize(
                forward
                + right * screen.x * tanHalfHorizontal
                + up * screen.y * tanHalfVertical
            );
        }

        float projectFisheye(
            vec3 spherePoint,
            float cameraYaw,
            float cameraPitch,
            float cameraRoll,
            vec3 cameraPosition,
            vec2 focalScale,
            vec2 opticalCenter,
            vec2 distortion,
            float maxTheta,
            float maxThetaBias,
            float mirror,
            out vec2 uv,
            out float theta,
            out float thetaLimit
        ) {
            vec3 cameraForward = directionFromYawPitch(cameraYaw, cameraPitch);
            vec3 cameraRight = normalize(vec3(cos(cameraYaw), 0.0, -sin(cameraYaw)));
            vec3 cameraUp = normalize(cross(cameraForward, cameraRight));
            float rollCos = cos(cameraRoll);
            float rollSin = sin(cameraRoll);
            vec3 rolledRight = cameraRight * rollCos + cameraUp * rollSin;
            vec3 rolledUp = cameraUp * rollCos - cameraRight * rollSin;
            vec3 cameraWorldRay = normalize(spherePoint - cameraPosition);
            vec3 cameraRay = vec3(
                dot(cameraWorldRay, rolledRight),
                dot(cameraWorldRay, rolledUp),
                dot(cameraWorldRay, cameraForward)
            );
            cameraRay.x = mix(cameraRay.x, -cameraRay.x, mirror);

            float radialLength = length(cameraRay.xy);
            theta = atan(radialLength, cameraRay.z);
            vec2 radialDirection = radialLength > 0.0001
                ? cameraRay.xy / radialLength
                : vec2(0.0);
            float theta2 = theta * theta;
            float correctedTheta = theta * (
                1.0 + distortion.x * theta2 + distortion.y * theta2 * theta2
            );
            uv = opticalCenter + radialDirection * correctedTheta * focalScale;
            thetaLimit = maxTheta;
            if (radialLength > 0.0001) {
                thetaLimit += maxThetaBias * cameraRay.x / radialLength;
            }
            return step(theta, thetaLimit) * inBounds(uv);
        }

        float edgeFeather(vec2 uv) {
            float edge = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
            return smoothstep(0.0, 0.045, edge);
        }

        float angularFeather(float theta, float thetaLimit) {
            return 1.0 - smoothstep(max(0.0, thetaLimit - uBlend), thetaLimit, theta);
        }

        void main() {
            // The sphere/equidistant projection follows comma-360-viewer's
            // camera model; this two-camera path keeps Wayon's softer seam.
            vec3 spherePoint = viewDirection() * uSphereRadius;
            vec2 wideUv;
            vec2 driverUv;
            float wideTheta;
            float driverTheta;
            float wideThetaLimit;
            float driverThetaLimit;
            float wideValid = projectFisheye(
                spherePoint, uWideYaw, uWidePitch, uWideRoll,
                uWidePosition, uWideFocalScale, uWideOpticalCenter,
                uWideFisheyeDistortion, uWideMaxTheta, uWideMaxThetaBias,
                0.0, wideUv, wideTheta, wideThetaLimit
            );
            float driverValid = projectFisheye(
                spherePoint, uDriverYaw, uDriverPitch, uDriverRoll,
                uDriverPosition, uDriverFocalScale, uDriverOpticalCenter,
                uDriverFisheyeDistortion, uDriverMaxTheta, uDriverMaxThetaBias,
                uDriverMirror, driverUv, driverTheta, driverThetaLimit
            );

            float wideWeight = wideValid * angularFeather(wideTheta, wideThetaLimit)
                * edgeFeather(wideUv) * uWideReady;
            float driverWeight = driverValid * angularFeather(driverTheta, driverThetaLimit)
                * edgeFeather(driverUv) * uDriverReady;
            wideWeight *= wideWeight;
            driverWeight *= driverWeight;
            if (wideWeight > 0.001) {
                driverWeight *= uDriverBlendReadiness;
            }
            float totalWeight = wideWeight + driverWeight;

            if (totalWeight < 0.001) {
                gl_FragColor = vec4(0.02, 0.02, 0.02, 1.0);
                return;
            }

            vec2 wideRadius = (wideUv - uWideOpticalCenter) * 2.0;
            vec2 driverRadius = (driverUv - uDriverOpticalCenter) * 2.0;
            vec3 wideColor = texture2D(uWide, clamp(wideUv, 0.0, 1.0)).rgb;
            vec3 driverColor = texture2D(uDriver, clamp(driverUv, 0.0, 1.0)).rgb;
            wideColor *= (1.0 + uWideVignette * dot(wideRadius, wideRadius)) * uWideExposureGain;
            driverColor *= (1.0 + uDriverVignette * dot(driverRadius, driverRadius)) * uDriverColorGain;

            vec3 wideLinear = pow(max(wideColor, vec3(0.0)), vec3(2.2));
            vec3 driverLinear = pow(max(driverColor, vec3(0.0)), vec3(2.2));
            vec3 colorLinear = (wideLinear * wideWeight + driverLinear * driverWeight) / totalWeight;
            gl_FragColor = vec4(pow(max(colorLinear, vec3(0.0)), vec3(1.0 / 2.2)), 1.0);
        }
    `;

    function compileShader(gl, type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            throw new Error(gl.getShaderInfoLog(shader) || "Shader compile failed");
        }
        return shader;
    }

    function createTexture(gl) {
        const texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(
            gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0,
            gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([4, 4, 4, 255]),
        );
        return texture;
    }

    function initGl() {
        if (glState) return true;
        const gl = canvas.getContext("webgl", {
            alpha: false,
            antialias: false,
            depth: false,
            desynchronized: true,
            powerPreference: "high-performance",
        });
        if (!gl) return false;

        const program = gl.createProgram();
        gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, vertexShader));
        gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, fragmentShader));
        gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            throw new Error(gl.getProgramInfoLog(program) || "Shader link failed");
        }
        gl.useProgram(program);

        const positions = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positions);
        gl.bufferData(
            gl.ARRAY_BUFFER,
            new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
            gl.STATIC_DRAW,
        );
        const position = gl.getAttribLocation(program, "aPosition");
        gl.enableVertexAttribArray(position);
        gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

        const uniforms = {};
        [
            "uWide", "uDriver", "uYaw", "uPitch", "uViewFov", "uAspect",
            "uProjectionMode", "uWideYaw", "uDriverYaw", "uWidePitch", "uDriverPitch",
            "uWideRoll", "uDriverRoll", "uWideFocalScale", "uDriverFocalScale",
            "uWideMaxTheta", "uDriverMaxTheta", "uWideMaxThetaBias", "uDriverMaxThetaBias",
            "uWidePosition", "uDriverPosition", "uSphereRadius",
            "uBlend", "uDriverMirror", "uWideReady", "uDriverReady",
            "uWideFisheyeDistortion", "uDriverFisheyeDistortion",
            "uWideOpticalCenter", "uDriverOpticalCenter",
            "uWideExposureGain", "uDriverBlendReadiness", "uDriverColorGain",
            "uWideVignette", "uDriverVignette",
        ].forEach((name) => { uniforms[name] = gl.getUniformLocation(program, name); });

        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
        gl.activeTexture(gl.TEXTURE0);
        const wideTexture = createTexture(gl);
        gl.activeTexture(gl.TEXTURE1);
        const driverTexture = createTexture(gl);
        gl.activeTexture(gl.TEXTURE0);
        glState = {
            gl,
            program,
            uniforms,
            textures: { wide: wideTexture, driver: driverTexture },
        };
        return true;
    }

    function resizeCanvas() {
        if (!glState) return;
        const maxSize = glState.gl.getParameter(glState.gl.MAX_RENDERBUFFER_SIZE);
        const requestedScale = Math.max(1, window.devicePixelRatio || 1);
        const scale = Math.min(
            requestedScale,
            maxSize / Math.max(1, canvas.clientWidth),
            maxSize / Math.max(1, canvas.clientHeight),
        );
        const width = Math.max(1, Math.round(canvas.clientWidth * scale));
        const height = Math.max(1, Math.round(canvas.clientHeight * scale));
        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
            glState.gl.viewport(0, 0, width, height);
        }
    }

    function edgeColorAverage(pixels, width, height, side) {
        const startX = Math.floor(width * (side === "left" ? 0.035 : 0.915));
        const endX = Math.ceil(width * (side === "left" ? 0.085 : 0.965));
        const startY = Math.floor(height * 0.2);
        const endY = Math.ceil(height * 0.8);
        const total = [0, 0, 0];
        let count = 0;

        for (let y = startY; y < endY; y += 2) {
            for (let x = startX; x < endX; x += 2) {
                const offset = (y * width + x) * 4;
                const red = pixels[offset];
                const green = pixels[offset + 1];
                const blue = pixels[offset + 2];
                const luminance = red * 0.2126 + green * 0.7152 + blue * 0.0722;
                if (luminance < 12 || luminance > 244) continue;
                total[0] += red;
                total[1] += green;
                total[2] += blue;
                count += 1;
            }
        }

        return count ? total.map((value) => value / count) : null;
    }

    function frameLuminanceStats(pixels, width, height) {
        let total = 0;
        const samples = [];
        for (let y = 2; y < height; y += 4) {
            for (let x = 2; x < width; x += 4) {
                const offset = (y * width + x) * 4;
                const luminance = pixels[offset] * 0.2126
                    + pixels[offset + 1] * 0.7152
                    + pixels[offset + 2] * 0.0722;
                total += luminance;
                samples.push(luminance);
            }
        }
        if (!samples.length) return { mean: 0, p90: 0 };
        samples.sort((left, right) => left - right);
        return {
            mean: total / samples.length,
            p90: samples[Math.min(samples.length - 1, Math.floor(samples.length * 0.9))],
        };
    }

    function updateWideStartupExposure(image, now) {
        if (!wideFirstFrameAt || now < nextWideExposureSampleAt) return;
        if (now - wideFirstFrameAt > WIDE_EXPOSURE_HOLD_MS + WIDE_EXPOSURE_FADE_MS) return;
        nextWideExposureSampleAt = now + WIDE_EXPOSURE_SAMPLE_INTERVAL_MS;

        const luminance = frameLuminanceStats(image.data, image.width, image.height);
        const targetGain = Math.max(
            1,
            Math.min(WIDE_EXPOSURE_MAX_GAIN, WIDE_EXPOSURE_TARGET_LUMA / Math.max(1, luminance.mean)),
        );
        if (wideExposureSamples === 0) {
            wideMeasuredExposureGain = targetGain;
        } else {
            wideMeasuredExposureGain = wideMeasuredExposureGain * 0.65 + targetGain * 0.35;
        }
        wideExposureSamples += 1;

        if (!wideExposureReady && (
            luminance.p90 >= WIDE_READY_P90_LUMA
            || now - wideFirstFrameAt >= WIDE_READY_TIMEOUT_MS
        )) {
            wideExposureReady = true;
            if (!savedPlayback) hideMessage();
        }
    }

    function smoothStep01(value) {
        const clamped = Math.max(0, Math.min(1, value));
        return clamped * clamped * (3 - 2 * clamped);
    }

    function currentWideExposureGain(now) {
        if (savedPlayback || !wideFirstFrameAt) return 1;
        const fadeProgress = (now - wideFirstFrameAt - WIDE_EXPOSURE_HOLD_MS) / WIDE_EXPOSURE_FADE_MS;
        return 1 + (wideMeasuredExposureGain - 1) * (1 - smoothStep01(fadeProgress));
    }

    function currentDriverBlendReadiness(now) {
        if (savedPlayback || !driverFirstFrameAt) return 1;
        const rampProgress = (now - driverFirstFrameAt - DRIVER_BLEND_HOLD_MS) / DRIVER_BLEND_RAMP_MS;
        return smoothStep01(rampProgress);
    }

    function resetStartupExposureState() {
        nextWideExposureSampleAt = 0;
        wideFirstFrameAt = 0;
        driverFirstFrameAt = 0;
        wideExposureSamples = 0;
        wideMeasuredExposureGain = 1;
        wideExposureReady = false;
    }

    function updateDriverColorGain() {
        const wide = edgeColorSamples.wide;
        const driver = edgeColorSamples.driver;
        if (!wide || !driver || Math.abs(wide.at - driver.at) > COLOR_SAMPLE_INTERVAL_MS * 2) return;

        const pairs = [
            [wide.right, driver.left],
            [wide.left, driver.right],
        ].filter(([wideColor, driverColor]) => wideColor && driverColor);
        if (!pairs.length) return;

        const target = [0, 1, 2].map((channel) => {
            const ratios = pairs
                .map(([wideColor, driverColor]) => wideColor[channel] / Math.max(8, driverColor[channel]))
                .filter(Number.isFinite);
            if (!ratios.length) return 1;
            return Math.max(0.72, Math.min(1.38, ratios.reduce((sum, value) => sum + value, 0) / ratios.length));
        });
        driverColorGain = driverColorGain.map((value, index) => value * 0.86 + target[index] * 0.14);
    }

    function sampleFrameEdges(name, frame, now) {
        const shouldSampleColor = now >= nextColorSampleAt[name];
        const shouldSampleWideExposure = name === "wide"
            && now >= nextWideExposureSampleAt
            && now - wideFirstFrameAt <= WIDE_EXPOSURE_HOLD_MS + WIDE_EXPOSURE_FADE_MS;
        if (!shouldSampleColor && !shouldSampleWideExposure) return;
        if (!colorSampleCanvas) {
            colorSampleCanvas = document.createElement("canvas");
            colorSampleCanvas.width = 96;
            colorSampleCanvas.height = 54;
            colorSampleContext = colorSampleCanvas.getContext("2d", { willReadFrequently: true });
        }
        if (!colorSampleContext) return;

        try {
            colorSampleContext.drawImage(frame, 0, 0, colorSampleCanvas.width, colorSampleCanvas.height);
            const image = colorSampleContext.getImageData(0, 0, colorSampleCanvas.width, colorSampleCanvas.height);
            if (shouldSampleWideExposure) updateWideStartupExposure(image, now);
            if (shouldSampleColor) {
                nextColorSampleAt[name] = now + COLOR_SAMPLE_INTERVAL_MS;
                edgeColorSamples[name] = {
                    at: now,
                    left: edgeColorAverage(image.data, image.width, image.height, "left"),
                    right: edgeColorAverage(image.data, image.width, image.height, "right"),
                };
                updateDriverColorGain();
            }
        } catch (error) {
            console.warn(`Wayon ${name} color sample failed`, error);
        }
    }

    function uploadFrame(name, textureUnit, now) {
        const stream = streams[name];
        if (!stream.frame || !glState) return;
        const { gl, textures } = glState;
        if (name === "wide" && !wideFirstFrameAt) wideFirstFrameAt = now;
        if (name === "driver" && !driverFirstFrameAt) driverFirstFrameAt = now;
        sampleFrameEdges(name, stream.frame, now);
        if (name === "wide" && !wideExposureReady
            && now - wideFirstFrameAt >= WIDE_READY_TIMEOUT_MS) {
            wideExposureReady = true;
            if (!savedPlayback) hideMessage();
        }
        gl.activeTexture(textureUnit);
        gl.bindTexture(gl.TEXTURE_2D, textures[name]);
        try {
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, stream.frame);
            stream.ready = true;
        } finally {
            stream.frame.close();
            stream.frame = null;
            stream.frameReceivedAt = 0;
        }
    }

    function discardPendingFrame(name) {
        const stream = streams[name];
        if (stream.frame) stream.frame.close();
        stream.frame = null;
        stream.frameReceivedAt = 0;
    }

    function uploadSynchronizedFrames(now) {
        const wideFrame = streams.wide.frame;
        const driverFrame = streams.driver.frame;
        if (wideFrame && driverFrame) {
            const timestampDelta = Number(wideFrame.timestamp) - Number(driverFrame.timestamp);
            if (Math.abs(timestampDelta) <= FRAME_SYNC_TOLERANCE_US) {
                uploadFrame("wide", glState.gl.TEXTURE0, now);
                uploadFrame("driver", glState.gl.TEXTURE1, now);
            } else {
                discardPendingFrame(timestampDelta < 0 ? "wide" : "driver");
            }
            return;
        }

        if (wideFrame && !streams.driver.ready &&
            now - streams.wide.frameReceivedAt >= SINGLE_CAMERA_STARTUP_MS) {
            uploadFrame("wide", glState.gl.TEXTURE0, now);
        } else if (driverFrame && !streams.wide.ready &&
            now - streams.driver.frameReceivedAt >= SINGLE_CAMERA_STARTUP_MS) {
            uploadFrame("driver", glState.gl.TEXTURE1, now);
        }
    }

    function metadataPair(value, fallback) {
        if (!Array.isArray(value) || value.length < 2) return fallback;
        const first = Number(value[0]);
        const second = Number(value[1]);
        return Number.isFinite(first) && Number.isFinite(second) ? [first, second] : fallback;
    }

    function metadataTriple(value, fallback) {
        if (!Array.isArray(value) || value.length < 3) return fallback;
        const output = value.slice(0, 3).map(Number);
        return output.every(Number.isFinite) ? output : fallback;
    }

    function drawPanorama(viewYaw, viewPitch, horizontalFov, width, height, projectionMode = 0) {
        const { gl, uniforms } = glState;
        const now = performance.now();
        const panorama = metadata?.panorama || {};
        const wideFocalScale = metadataPair(panorama.wideFocalScale, [0.31640625, 0.55953947]);
        const driverFocalScale = metadataPair(panorama.driverFocalScale, [0.31640625, 0.55953947]);
        const wideDistortion = metadataPair(panorama.wideFisheyeDistortion, [-0.035, 0]);
        const driverDistortion = metadataPair(panorama.driverFisheyeDistortion, [-0.035, 0]);
        const wideCenter = metadataPair(panorama.wideOpticalCenter, [0.5, 0.5]);
        const driverCenter = metadataPair(panorama.driverOpticalCenter, [0.5, 0.5]);
        const widePosition = metadataTriple(panorama.widePositionM, [-0.2, 0, 0]);
        const driverPosition = metadataTriple(panorama.driverPositionM, [0, -0.435, 0.03]);

        gl.viewport(0, 0, width, height);
        gl.useProgram(glState.program);
        gl.uniform1i(uniforms.uWide, 0);
        gl.uniform1i(uniforms.uDriver, 1);
        gl.uniform1f(uniforms.uYaw, viewYaw);
        gl.uniform1f(uniforms.uPitch, viewPitch);
        gl.uniform1f(uniforms.uViewFov, horizontalFov);
        gl.uniform1f(uniforms.uAspect, width / Math.max(1, height));
        gl.uniform1f(uniforms.uProjectionMode, projectionMode);
        gl.uniform1f(uniforms.uWideYaw, Number(panorama.wideYawDeg ?? 0) * DEG);
        gl.uniform1f(uniforms.uDriverYaw, Number(panorama.driverYawDeg ?? 180) * DEG);
        gl.uniform1f(uniforms.uWidePitch, Number(panorama.widePitchDeg ?? -6.5) * DEG);
        gl.uniform1f(uniforms.uDriverPitch, Number(panorama.driverPitchDeg ?? -14) * DEG);
        gl.uniform1f(uniforms.uWideRoll, Number(panorama.wideRollDeg ?? 0) * DEG);
        gl.uniform1f(uniforms.uDriverRoll, Number(panorama.driverRollDeg ?? 0) * DEG);
        gl.uniform2f(uniforms.uWideFocalScale, wideFocalScale[0], wideFocalScale[1]);
        gl.uniform2f(uniforms.uDriverFocalScale, driverFocalScale[0], driverFocalScale[1]);
        gl.uniform1f(uniforms.uWideMaxTheta, Number(panorama.wideMaxThetaDeg ?? 102.5) * DEG);
        gl.uniform1f(uniforms.uDriverMaxTheta, Number(panorama.driverMaxThetaDeg ?? 102.5) * DEG);
        gl.uniform1f(uniforms.uWideMaxThetaBias, Number(panorama.wideMaxThetaBiasDeg ?? 0) * DEG);
        gl.uniform1f(uniforms.uDriverMaxThetaBias, Number(panorama.driverMaxThetaBiasDeg ?? 0) * DEG);
        gl.uniform3f(uniforms.uWidePosition, widePosition[0], widePosition[1], widePosition[2]);
        gl.uniform3f(uniforms.uDriverPosition, driverPosition[0], driverPosition[1], driverPosition[2]);
        gl.uniform1f(uniforms.uSphereRadius, Number(panorama.sphereRadiusM ?? 10));
        gl.uniform1f(uniforms.uBlend, Number(panorama.blendDeg ?? 24) * DEG);
        gl.uniform1f(uniforms.uDriverMirror, panorama.driverMirror === false ? 0 : 1);
        gl.uniform1f(uniforms.uWideReady, streams.wide.ready ? 1 : 0);
        gl.uniform1f(uniforms.uDriverReady, streams.driver.ready ? 1 : 0);
        gl.uniform2f(uniforms.uWideFisheyeDistortion, wideDistortion[0], wideDistortion[1]);
        gl.uniform2f(uniforms.uDriverFisheyeDistortion, driverDistortion[0], driverDistortion[1]);
        gl.uniform2f(uniforms.uWideOpticalCenter, wideCenter[0], wideCenter[1]);
        gl.uniform2f(uniforms.uDriverOpticalCenter, driverCenter[0], driverCenter[1]);
        gl.uniform1f(uniforms.uWideExposureGain, currentWideExposureGain(now));
        gl.uniform1f(uniforms.uDriverBlendReadiness, currentDriverBlendReadiness(now));
        gl.uniform3f(uniforms.uDriverColorGain, driverColorGain[0], driverColorGain[1], driverColorGain[2]);
        gl.uniform1f(uniforms.uWideVignette, Number(panorama.wideVignetteCompensation ?? 0.045));
        gl.uniform1f(uniforms.uDriverVignette, Number(panorama.driverVignetteCompensation ?? 0.045));
        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    function sendClientControl(commandType, payload = new Uint8Array(0)) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            showSaveToast("Live 연결 후 저장할 수 있습니다.");
            return false;
        }
        const body = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
        const packet = new Uint8Array(9 + body.length);
        packet.set(CONTROL_MAGIC, 0);
        packet[4] = commandType;
        new DataView(packet.buffer).setUint32(5, body.length, false);
        packet.set(body, 9);
        socket.send(packet.buffer);
        return true;
    }

    function jpegBlob(sourceCanvas) {
        return new Promise((resolve, reject) => {
            sourceCanvas.toBlob(
                (blob) => blob ? resolve(blob) : reject(new Error("JPEG encoding failed")),
                "image/jpeg",
                1.0,
            );
        });
    }

    async function capturePanoramaPhoto() {
        if (photoCaptureBusy) return;
        if (!glState || !streams.wide.ready || !streams.driver.ready) {
            showSaveToast("두 카메라 준비 후 저장할 수 있습니다.");
            return;
        }

        photoCaptureBusy = true;
        photoButton.disabled = true;
        showSaveToast("360° 사진 생성 중", 6000);
        const { gl } = glState;
        let framebuffer = null;
        let captureTexture = null;
        try {
            const cameraWidth = Math.max(1, Number(metadata?.width) || 1344);
            const cameraFov = Math.max(1, Number(metadata?.panorama?.wideFovDeg) || 205);
            const sourceDensityWidth = Math.ceil(cameraWidth * 360 / cameraFov);
            const width = Math.min(sourceDensityWidth, gl.getParameter(gl.MAX_TEXTURE_SIZE));
            const height = Math.max(1, Math.round(width * 128 / 360));
            framebuffer = gl.createFramebuffer();
            captureTexture = gl.createTexture();
            gl.activeTexture(gl.TEXTURE2);
            gl.bindTexture(gl.TEXTURE_2D, captureTexture);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
            gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
            gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, captureTexture, 0);
            if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
                throw new Error("Panorama framebuffer incomplete");
            }

            drawPanorama(0, 0, Math.PI * 2, width, height, 1);
            const pixels = new Uint8Array(width * height * 4);
            gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);

            const outputCanvas = document.createElement("canvas");
            outputCanvas.width = width;
            outputCanvas.height = height;
            const outputContext = outputCanvas.getContext("2d");
            if (!outputContext) throw new Error("Panorama canvas unavailable");
            const image = outputContext.createImageData(width, height);
            const rowBytes = width * 4;
            for (let row = 0; row < height; row += 1) {
                const sourceOffset = (height - row - 1) * rowBytes;
                image.data.set(pixels.subarray(sourceOffset, sourceOffset + rowBytes), row * rowBytes);
            }
            outputContext.putImageData(image, 0, 0);
            gl.bindFramebuffer(gl.FRAMEBUFFER, null);
            gl.deleteFramebuffer(framebuffer);
            framebuffer = null;
            gl.deleteTexture(captureTexture);
            captureTexture = null;
            gl.activeTexture(gl.TEXTURE0);
            drawPanorama(yaw, pitch, viewFov, canvas.width, canvas.height);
            const blob = await jpegBlob(outputCanvas);
            const payload = new Uint8Array(await blob.arrayBuffer());
            if (sendClientControl(CONTROL_PHOTO, payload)) showSaveToast("360° 사진 업로드 중", 6000);
        } catch (error) {
            console.error("Wayon panorama capture failed", error);
            showSaveToast("360° 사진 생성에 실패했습니다.");
        } finally {
            gl.bindFramebuffer(gl.FRAMEBUFFER, null);
            if (framebuffer) gl.deleteFramebuffer(framebuffer);
            if (captureTexture) gl.deleteTexture(captureTexture);
            gl.activeTexture(gl.TEXTURE0);
            drawPanorama(yaw, pitch, viewFov, canvas.width, canvas.height);
            photoCaptureBusy = false;
            photoButton.disabled = false;
        }
    }

    function requestClip(durationSeconds) {
        if (sendClientControl(CONTROL_CLIP, new Uint8Array([durationSeconds]))) {
            showSaveToast(`최근 ${durationSeconds}초 클립 준비 중`, 5000);
        }
    }

    function parseStoredZip(buffer) {
        const bytes = new Uint8Array(buffer);
        const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
        const decoder = new TextDecoder();
        const entries = new Map();
        let offset = 0;

        while (offset + 4 <= bytes.length) {
            const signature = view.getUint32(offset, true);
            if (signature !== 0x04034b50) break;
            if (offset + 30 > bytes.length) throw new Error("Invalid ZIP header");
            const flags = view.getUint16(offset + 6, true);
            const method = view.getUint16(offset + 8, true);
            const compressedSize = view.getUint32(offset + 18, true);
            const nameLength = view.getUint16(offset + 26, true);
            const extraLength = view.getUint16(offset + 28, true);
            if ((flags & 0x08) !== 0 || method !== 0) throw new Error("Unsupported ZIP encoding");

            const nameStart = offset + 30;
            const dataStart = nameStart + nameLength + extraLength;
            const dataEnd = dataStart + compressedSize;
            if (dataEnd > bytes.length) throw new Error("Truncated ZIP entry");
            const name = decoder.decode(bytes.subarray(nameStart, nameStart + nameLength));
            entries.set(name, bytes.slice(dataStart, dataEnd));
            offset = dataEnd;
        }
        return entries;
    }

    function splitAnnexBFrames(bytes) {
        const starts = [];
        for (let index = 0; index + 3 < bytes.length;) {
            if (bytes[index] === 0 && bytes[index + 1] === 0 && bytes[index + 2] === 0 && bytes[index + 3] === 1) {
                starts.push({ start: index, payload: index + 4 });
                index += 4;
            } else if (bytes[index] === 0 && bytes[index + 1] === 0 && bytes[index + 2] === 1) {
                starts.push({ start: index, payload: index + 3 });
                index += 3;
            } else {
                index += 1;
            }
        }

        const frames = [];
        let pendingStart = -1;
        for (let index = 0; index < starts.length; index += 1) {
            const nal = starts[index];
            const end = index + 1 < starts.length ? starts[index + 1].start : bytes.length;
            const type = bytes[nal.payload] & 0x1f;
            if (type === 1 || type === 5) {
                const start = pendingStart >= 0 ? pendingStart : nal.start;
                frames.push({ data: bytes.slice(start, end), key: type === 5 });
                pendingStart = -1;
            } else if (pendingStart < 0) {
                pendingStart = nal.start;
            }
        }
        return frames;
    }

    function createSavedTrack(bytes, durationMs) {
        const frames = splitAnnexBFrames(bytes);
        const divisor = Math.max(1, frames.length - 1);
        return frames.map((frame, index) => {
            const atMs = durationMs * index / divisor;
            return { ...frame, atMs, timestamp: Math.round(atMs * 1000) };
        });
    }

    function playbackClock(valueMs) {
        const seconds = Math.max(0, Math.floor(Number(valueMs) / 1000));
        return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    }

    function updatePlaybackUi() {
        if (!savedPlayback) {
            playbackProgress.style.width = "0%";
            playbackTime.textContent = "0:00 / 0:00";
            return;
        }
        const duration = Math.max(1, savedPlayback.durationMs);
        const progress = Math.max(0, Math.min(1, savedPlayback.positionMs / duration));
        playbackProgress.style.width = `${(progress * 100).toFixed(2)}%`;
        playbackTime.textContent = `${playbackClock(savedPlayback.positionMs)} / ${playbackClock(duration)}`;
        const icon = playbackToggle.querySelector("i");
        if (icon) icon.className = savedPlayback.finished ? "fas fa-redo" : (savedPlayback.paused ? "fas fa-play" : "fas fa-pause");
        playbackToggle.setAttribute("aria-label", savedPlayback.finished ? "다시 재생" : (savedPlayback.paused ? "재생" : "일시정지"));
    }

    function pumpSavedPlayback(now) {
        if (!savedPlayback) return;
        if (!savedPlayback.paused) {
            savedPlayback.positionMs = Math.min(savedPlayback.durationMs, now - savedPlayback.startedAt);
            for (const name of ["wide", "driver"]) {
                const track = savedPlayback.tracks[name];
                while (savedPlayback.indices[name] < track.length) {
                    const frame = track[savedPlayback.indices[name]];
                    if (frame.atMs > savedPlayback.positionMs + 90) break;
                    const decoder = decoderFor(name);
                    if (decoder.decodeQueueSize >= 2) break;
                    decodeVideo(name, frame.data, frame.key, frame.timestamp);
                    savedPlayback.indices[name] += 1;
                }
            }
            if (savedPlayback.positionMs >= savedPlayback.durationMs) {
                savedPlayback.positionMs = savedPlayback.durationMs;
                savedPlayback.paused = true;
                savedPlayback.finished = true;
                setStatus("재생 완료");
            }
        }
        updatePlaybackUi();
    }

    function restartSavedPlayback() {
        if (!savedPlayback) return;
        closeDecoders();
        savedPlayback.indices = { wide: 0, driver: 0 };
        savedPlayback.positionMs = 0;
        savedPlayback.startedAt = performance.now();
        savedPlayback.paused = false;
        savedPlayback.finished = false;
        showMessage("저장 영상 준비 중", false, true);
        setStatus("저장 영상");
        updatePlaybackUi();
    }

    function clearSavedPlayback() {
        savedLoadSequence += 1;
        savedPlayback = null;
        savedPlaybackRequest = null;
        overlay.classList.remove("playback");
        playbackBar.hidden = true;
        updatePlaybackUi();
    }

    function prepareSavedPlaybackOverlay() {
        intentionalClose = true;
        sessionRequestPending = false;
        stopHeartbeat();
        clearStartupTimer();
        clearTimeout(reconnectTimer);
        reconnectTimer = 0;
        if (socket) socket.close(1000, "saved playback");
        socket = null;
        closeDecoders();
        receiveBuffer = new Uint8Array(0);
        terminalState = null;
        overlay.classList.add("active", "playback");
        overlay.setAttribute("aria-hidden", "false");
        playbackBar.hidden = false;
        hideSaveToast();
        hideImpactPanel();
        yaw = 0;
        pitch = 0;
        viewFov = 78 * DEG;
        yawVelocity = 0;
        pitchVelocity = 0;
        driverColorGain = [1, 1, 1];
        resetStartupExposureState();
        nextColorSampleAt.wide = 0;
        nextColorSampleAt.driver = 0;
        edgeColorSamples.wide = null;
        edgeColorSamples.driver = null;
        lastRenderAt = 0;
        status.classList.remove("live");
        suspendNativeRefresh(true);
        if (!animationFrame) animationFrame = requestAnimationFrame(render);
    }

    window.startWayonSavedClip = async (request) => {
        if (typeof VideoDecoder === "undefined" || typeof EncodedVideoChunk === "undefined") {
            showMessage("Android System WebView 업데이트가 필요합니다.", false, false);
            return;
        }
        try {
            if (!initGl()) throw new Error("WebGL unavailable");
        } catch (error) {
            console.error("Wayon saved playback init failed", error);
            showMessage("360° 화면을 초기화할 수 없습니다.", false, false);
            return;
        }

        const loadSequence = ++savedLoadSequence;
        savedPlaybackRequest = request;
        savedPlayback = null;
        prepareSavedPlaybackOverlay();
        showMessage("저장 영상 불러오는 중", false, true);
        setStatus("저장 영상");
        updatePlaybackUi();

        try {
            const response = await fetch(request.url, {
                headers: { Authorization: `Bearer ${request.token}` },
                cache: "no-store",
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const entries = parseStoredZip(await response.arrayBuffer());
            const manifestBytes = entries.get("manifest.json");
            const wideBytes = entries.get("wide.h264");
            const driverBytes = entries.get("driver.h264");
            if (!manifestBytes || !wideBytes || !driverBytes) throw new Error("Missing saved video stream");

            const manifest = JSON.parse(new TextDecoder().decode(manifestBytes));
            const durationSeconds = Math.max(
                Number(manifest?.cameras?.wide?.durationSeconds) || 0,
                Number(manifest?.cameras?.driver?.durationSeconds) || 0,
                Number(request?.capture?.durationS) || 0,
                0.1,
            );
            const durationMs = durationSeconds * 1000;
            const tracks = {
                wide: createSavedTrack(wideBytes, durationMs),
                driver: createSavedTrack(driverBytes, durationMs),
            };
            if (!tracks.wide.length || !tracks.driver.length) throw new Error("No decodable saved frames");
            if (loadSequence !== savedLoadSequence || !overlay.classList.contains("active")) return;

            metadata = {
                codec: manifest.codec || "avc1.640020",
                width: manifest.width,
                height: manifest.height,
                panorama: manifest.panorama || {},
            };
            savedPlayback = {
                tracks,
                indices: { wide: 0, driver: 0 },
                durationMs,
                positionMs: 0,
                startedAt: performance.now(),
                paused: false,
                finished: false,
            };
            setStatus("저장 영상");
            updatePlaybackUi();
        } catch (error) {
            if (loadSequence !== savedLoadSequence) return;
            console.error("Wayon saved playback failed", error);
            showMessage("저장 영상을 재생할 수 없습니다.", true, false);
            setStatus("재생 실패");
        }
    };

    function wrapAngle(value) {
        const full = Math.PI * 2;
        return ((value + Math.PI) % full + full) % full - Math.PI;
    }

    function compassLabel() {
        const degree = ((yaw / DEG) % 360 + 360) % 360;
        if (degree < 45 || degree >= 315) return "FRONT";
        if (degree < 135) return "RIGHT";
        if (degree < 225) return "REAR";
        return "LEFT";
    }

    function render(now) {
        if (!overlay.classList.contains("active") || !glState) return;
        animationFrame = requestAnimationFrame(render);
        resizeCanvas();

        const delta = lastRenderAt ? Math.min(0.05, (now - lastRenderAt) / 1000) : 0;
        lastRenderAt = now;
        if (pointers.size === 0 && delta > 0) {
            yaw = wrapAngle(yaw + yawVelocity * delta);
            pitch = Math.max(-55 * DEG, Math.min(45 * DEG, pitch + pitchVelocity * delta));
            const friction = Math.exp(-4.5 * delta);
            yawVelocity *= friction;
            pitchVelocity *= friction;
        }

        pumpSavedPlayback(now);
        uploadSynchronizedFrames(now);
        drawPanorama(yaw, pitch, viewFov, canvas.width, canvas.height);
        compass.textContent = compassLabel();
    }

    function setStatus(text, isLive = false) {
        statusText.textContent = text;
        status.classList.toggle("live", isLive);
    }

    function showMessage(text, canRetry = false, loading = false) {
        message.classList.remove("hidden");
        messageText.textContent = text;
        retry.hidden = !canRetry;
        spinner.hidden = !loading;
    }

    function hideMessage() {
        message.classList.add("hidden");
    }

    function hideImpactPanel() {
        impactRequestSequence += 1;
        impactPanel.hidden = true;
    }

    function showSaveToast(text, durationMs = 2800) {
        clearTimeout(saveToastTimer);
        saveToast.textContent = text;
        saveToast.hidden = false;
        saveToastTimer = setTimeout(() => { saveToast.hidden = true; }, durationMs);
    }

    function hideSaveToast() {
        clearTimeout(saveToastTimer);
        saveToastTimer = 0;
        saveToast.hidden = true;
    }

    function impactDateTime(value) {
        const parsed = Date.parse(value || "");
        if (!Number.isFinite(parsed)) return "시각 정보 없음";
        return new Intl.DateTimeFormat("ko-KR", {
            timeZone: "Asia/Seoul",
            month: "numeric",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }).format(new Date(parsed));
    }

    function impactLocationText(impact) {
        const latitude = Number(impact?.latitude);
        const longitude = Number(impact?.longitude);
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude) ||
            Math.abs(latitude) < 0.001 || Math.abs(longitude) < 0.001) {
            return "위치 정보 없음";
        }
        return `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
    }

    async function refreshImpactPanel() {
        const token = window.getWayonCloudViewToken?.() ||
            document.getElementById("wayon-cloud-key-input")?.value?.trim() || "";
        if (!token) {
            hideImpactPanel();
            return;
        }

        const requestSequence = ++impactRequestSequence;
        try {
            const cloudBaseUrl = window.getWayonCloudBaseUrl?.() || "https://wayon-cloud.hyuklee.workers.dev";
            const response = await fetch(`${cloudBaseUrl.replace(/\/$/, "")}/api/impacts?limit=1`, {
                cache: "no-store",
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const impact = (await response.json())?.impacts?.[0];
            if (requestSequence !== impactRequestSequence || !impact) return hideImpactPanel();

            const dynamicG = Number(impact.peak_dynamic_g);
            const totalG = Number(impact.peak_total_g);
            const force = Number.isFinite(dynamicG) ? dynamicG : totalG;
            const locked = impact.vehicle_locked;
            impactTime.textContent = impactDateTime(impact.detected_at);
            impactForce.textContent = Number.isFinite(force) ? `${force.toFixed(2)} g` : "충격 감지";
            impactLocation.textContent = impactLocationText(impact);
            impactLock.textContent = locked === 1 || locked === true
                ? "잠금 상태"
                : (locked === 0 || locked === false ? "잠금 해제" : "잠금 상태 미상");
            impactPanel.hidden = false;
        } catch (error) {
            console.warn("Wayon impact panel refresh failed", error);
            if (requestSequence === impactRequestSequence) hideImpactPanel();
        }
    }

    function clearStartupTimer() {
        clearTimeout(startupTimer);
        startupTimer = 0;
    }

    function closeDecoders() {
        Object.values(streams).forEach((stream) => {
            if (stream.frame) stream.frame.close();
            stream.frame = null;
            stream.frameReceivedAt = 0;
            stream.ready = false;
            stream.keySeen = false;
            stream.droppingUntilKey = false;
            stream.lastTimestamp = -1;
            if (stream.decoder) {
                try { stream.decoder.close(); } catch (_) {}
            }
            stream.decoder = null;
        });
    }

    function decoderFor(name) {
        const stream = streams[name];
        if (stream.decoder) return stream.decoder;
        const decoder = new VideoDecoder({
            output(frame) {
                if (stream.frame) stream.frame.close();
                stream.frame = frame;
                stream.frameReceivedAt = performance.now();
                frameCounter += 1;
                if (savedPlayback) {
                    clearStartupTimer();
                    hideMessage();
                } else if (name === "wide") {
                    clearStartupTimer();
                }
            },
            error(error) {
                console.error(`Wayon ${name} decoder error`, error);
                setStatus("디코더 오류");
                clearStartupTimer();
                showMessage(savedPlaybackRequest ? "저장 영상을 디코딩할 수 없습니다." : "카메라 영상을 디코딩할 수 없습니다.", true, false);
            },
        });
        decoder.configure({
            codec: metadata?.codec || "avc1.640020",
            hardwareAcceleration: "prefer-hardware",
            optimizeForLatency: true,
        });
        stream.decoder = decoder;
        return decoder;
    }

    function resetDecoderAtKeyFrame(stream) {
        if (stream.frame) stream.frame.close();
        stream.frame = null;
        stream.frameReceivedAt = 0;
        if (stream.decoder) {
            try { stream.decoder.close(); } catch (_) {}
        }
        stream.decoder = null;
        stream.keySeen = false;
        stream.droppingUntilKey = false;
        stream.lastTimestamp = -1;
    }

    function decodeVideo(name, payload, keyFrame, timestamp) {
        const stream = streams[name];
        if (stream.droppingUntilKey && !keyFrame) return;

        if (!keyFrame && stream.decoder?.decodeQueueSize > MAX_DECODE_QUEUE) {
            // H.264 delta frames depend on every preceding frame. Once one is
            // skipped, wait for the next key frame instead of decoding a
            // corrupted prediction chain that leaves trails on screen.
            stream.droppingUntilKey = true;
            return;
        }
        if (keyFrame && (stream.droppingUntilKey || stream.decoder?.decodeQueueSize > MAX_DECODE_QUEUE)) {
            resetDecoderAtKeyFrame(stream);
        }
        if (!stream.keySeen && !keyFrame) return;
        if (keyFrame) stream.keySeen = true;
        const decoder = decoderFor(name);
        const safeTimestamp = Math.max(stream.lastTimestamp + 1, timestamp);
        stream.lastTimestamp = safeTimestamp;
        decoder.decode(new EncodedVideoChunk({
            type: keyFrame ? "key" : "delta",
            timestamp: safeTimestamp,
            data: payload,
        }));
    }

    function handleCaptureStatus(data) {
        const duration = Math.max(0, Math.round(Number(data.durationSeconds) || 0));
        const label = data.kind === "photo" ? "360° 사진" : `${duration || ""}초 클립`.trim();
        if (data.captureState === "saved") {
            showSaveToast(`${label}이 Wayon Cloud에 저장됐습니다.`, 4200);
            window.dispatchEvent(new CustomEvent("wayon-live-capture-saved", { detail: data }));
        } else if (data.captureState === "uploading") {
            showSaveToast(`${label} 업로드 중`, 6000);
        } else if (data.captureState === "buffering") {
            showSaveToast(`클립 버퍼 준비 중 · 현재 ${duration}초`, 3600);
        } else {
            showSaveToast(`${label || "Live 기록"} 저장에 실패했습니다.`, 3600);
        }
    }

    function handleControl(frameType, payload) {
        const data = JSON.parse(new TextDecoder().decode(payload));
        if (frameType === FRAME_METADATA) {
            metadata = data;
            setStatus("카메라 준비 중");
            return;
        }

        if (data.state === "capture") {
            handleCaptureStatus(data);
            return;
        }

        if (data.state === "live") {
            reconnectAttempts = 0;
            setStatus("LIVE", true);
            return;
        }
        terminalState = data.state || "error";
        const messages = {
            onroad: "주행 중에는 Live를 사용할 수 없습니다.",
            busy: "카메라가 사용 중입니다.",
            expired: "Live 시간이 종료되었습니다.",
        };
        showMessage(messages[data.state] || "Live 연결이 종료되었습니다.", true, false);
        setStatus("연결 종료");
    }

    function consumeFrames() {
        let offset = 0;
        while (receiveBuffer.length - offset >= HEADER_SIZE) {
            const view = new DataView(receiveBuffer.buffer, receiveBuffer.byteOffset + offset);
            if (view.getUint8(0) !== 87 || view.getUint8(1) !== 76 ||
                view.getUint8(2) !== 86 || view.getUint8(3) !== 49) {
                throw new Error("Invalid Wayon Live frame");
            }
            const frameType = view.getUint8(4);
            const flags = view.getUint8(5);
            const timestamp = view.getUint32(12) * 4294967296 + view.getUint32(16);
            const payloadSize = view.getUint32(20);
            if (payloadSize > MAX_PAYLOAD_SIZE) throw new Error("Wayon Live frame too large");
            if (receiveBuffer.length - offset < HEADER_SIZE + payloadSize) break;

            const payloadStart = offset + HEADER_SIZE;
            const payload = receiveBuffer.slice(payloadStart, payloadStart + payloadSize);
            if (frameType === FRAME_WIDE) {
                decodeVideo("wide", payload, Boolean(flags & FLAG_KEY), timestamp);
            } else if (frameType === FRAME_DRIVER) {
                decodeVideo("driver", payload, Boolean(flags & FLAG_KEY), timestamp);
            } else if (frameType === FRAME_METADATA || frameType === FRAME_STATUS) {
                handleControl(frameType, payload);
            }
            offset += HEADER_SIZE + payloadSize;
        }
        receiveBuffer = receiveBuffer.slice(offset);
    }

    function appendChunk(chunk) {
        const incoming = new Uint8Array(chunk);
        if (receiveBuffer.length === 0) {
            receiveBuffer = incoming;
            consumeFrames();
            return;
        }
        const merged = new Uint8Array(receiveBuffer.length + incoming.length);
        merged.set(receiveBuffer);
        merged.set(incoming, receiveBuffer.length);
        receiveBuffer = merged;
        consumeFrames();
    }

    function stopHeartbeat() {
        if (heartbeatTimer) clearInterval(heartbeatTimer);
        heartbeatTimer = 0;
    }

    function startHeartbeat(currentSocket) {
        stopHeartbeat();
        const sendHeartbeat = () => {
            if (socket !== currentSocket || currentSocket.readyState !== WebSocket.OPEN) return;
            try {
                currentSocket.send("WLP1");
            } catch (error) {
                console.warn("Wayon Live heartbeat failed", error);
            }
        };
        sendHeartbeat();
        heartbeatTimer = setInterval(sendHeartbeat, 3000);
    }

    function suspendNativeRefresh(suspended) {
        if (nativeRefreshSuspended === suspended) return;
        nativeRefreshSuspended = suspended;
        window.Android?.setWayonLiveActive?.(suspended);
    }

    function connect(websocketUrl, protocol) {
        stopHeartbeat();
        if (socket) {
            intentionalClose = true;
            socket.close(1000, "replaced");
            socket = null;
        }
        sessionRequestPending = false;
        intentionalClose = false;
        terminalState = null;
        receiveBuffer = new Uint8Array(0);
        const currentSocket = new WebSocket(websocketUrl, protocol);
        socket = currentSocket;
        currentSocket.binaryType = "arraybuffer";
        currentSocket.onopen = () => {
            if (socket !== currentSocket) return;
            startHeartbeat(currentSocket);
            setStatus("카메라 연결 중");
            clearStartupTimer();
            startupTimer = setTimeout(() => {
                if (socket !== currentSocket || streams.wide.ready || streams.driver.ready) return;
                intentionalClose = true;
                stopHeartbeat();
                currentSocket.close(1000, "video timeout");
                if (socket === currentSocket) socket = null;
                showMessage("차량 영상이 도착하지 않습니다. 다시 연결해 주세요.", true, false);
                setStatus("영상 대기 시간 초과");
            }, 12000);
        };
        currentSocket.onmessage = async (event) => {
            if (socket !== currentSocket) return;
            try {
                const chunk = event.data instanceof Blob ? await event.data.arrayBuffer() : event.data;
                if (socket !== currentSocket) return;
                appendChunk(chunk);
            } catch (error) {
                console.error("Wayon Live protocol error", error);
                showMessage("영상 데이터를 처리할 수 없습니다.", true, false);
                currentSocket.close();
            }
        };
        currentSocket.onerror = () => {
            if (socket === currentSocket) setStatus("연결 오류");
        };
        currentSocket.onclose = () => {
            if (socket !== currentSocket) return;
            stopHeartbeat();
            socket = null;
            clearStartupTimer();
            if (intentionalClose || !overlay.classList.contains("active")) return;
            if (terminalState === "busy" && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts += 1;
                showMessage("카메라 준비가 끝나기를 기다리는 중", false, true);
                setStatus("재연결 중");
                clearTimeout(reconnectTimer);
                reconnectTimer = setTimeout(() => requestSession(false), 1500);
            } else if (!terminalState && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts += 1;
                showMessage("차량 Live 연결 복구 중", false, true);
                setStatus("재연결 중");
                clearTimeout(reconnectTimer);
                reconnectTimer = setTimeout(() => requestSession(false), 1000);
            } else if (!terminalState) {
                showMessage("차량 Live 연결이 종료되었습니다.", true, false);
                setStatus("연결 종료");
            }
        };
    }

    function requestSession(resetAttempts = true) {
        if (sessionRequestPending) return;
        sessionRequestPending = true;
        if (resetAttempts) reconnectAttempts = 0;
        closeDecoders();
        receiveBuffer = new Uint8Array(0);
        showMessage("차량 카메라 연결 중", false, true);
        setStatus("연결 중");
        if (!window.Android?.requestWayonLiveSession) {
            sessionRequestPending = false;
            showMessage("앱에서만 Live를 사용할 수 있습니다.", false, false);
            return;
        }
        window.Android.requestWayonLiveSession();
    }

    window.onWayonLiveSession = (websocketUrl, protocol) => {
        sessionRequestPending = false;
        if (!overlay.classList.contains("active") || overlay.classList.contains("playback")) return;
        connect(websocketUrl, protocol);
    };

    window.onWayonLiveSessionError = (error) => {
        sessionRequestPending = false;
        if (!overlay.classList.contains("active") || overlay.classList.contains("playback")) return;
        showMessage(error || "차량 Live 연결에 실패했습니다.", true, false);
        setStatus("연결 실패");
    };

    window.startWayonLiveView = () => {
        if (overlay.classList.contains("active") && (sessionRequestPending || socket)) return;
        if (typeof VideoDecoder === "undefined" || typeof EncodedVideoChunk === "undefined") {
            overlay.classList.add("active");
            overlay.setAttribute("aria-hidden", "false");
            showMessage("Android System WebView 업데이트가 필요합니다.", false, false);
            return;
        }
        try {
            if (!initGl()) throw new Error("WebGL unavailable");
        } catch (error) {
            console.error("Wayon Live WebGL init failed", error);
            overlay.classList.add("active");
            overlay.setAttribute("aria-hidden", "false");
            showMessage("360° 화면을 초기화할 수 없습니다.", false, false);
            return;
        }

        clearSavedPlayback();
        overlay.classList.add("active");
        overlay.setAttribute("aria-hidden", "false");
        yaw = 0;
        pitch = 0;
        viewFov = 78 * DEG;
        yawVelocity = 0;
        pitchVelocity = 0;
        metadata = null;
        hideSaveToast();
        driverColorGain = [1, 1, 1];
        resetStartupExposureState();
        nextColorSampleAt.wide = 0;
        nextColorSampleAt.driver = 0;
        edgeColorSamples.wide = null;
        edgeColorSamples.driver = null;
        lastRenderAt = 0;
        fpsStartedAt = performance.now();
        if (!animationFrame) animationFrame = requestAnimationFrame(render);
        suspendNativeRefresh(true);
        refreshImpactPanel();
        requestSession();
    };

    window.stopWayonLiveView = () => {
        intentionalClose = true;
        sessionRequestPending = false;
        stopHeartbeat();
        clearStartupTimer();
        clearTimeout(reconnectTimer);
        reconnectTimer = 0;
        if (socket) socket.close(1000, "viewer closed");
        socket = null;
        closeDecoders();
        clearSavedPlayback();
        receiveBuffer = new Uint8Array(0);
        pointers.clear();
        pinchStart = null;
        if (animationFrame) cancelAnimationFrame(animationFrame);
        animationFrame = 0;
        overlay.classList.remove("active");
        overlay.setAttribute("aria-hidden", "true");
        status.classList.remove("live");
        hideSaveToast();
        hideImpactPanel();
        suspendNativeRefresh(false);
    };

    function pointerDistance() {
        if (pointers.size !== 2) return 0;
        const values = [...pointers.values()];
        return Math.hypot(values[0].x - values[1].x, values[0].y - values[1].y);
    }

    function horizontalViewFov() {
        const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
        return 2 * Math.atan(Math.tan(viewFov * 0.5) * aspect);
    }

    canvas.addEventListener("pointerdown", (event) => {
        canvas.setPointerCapture(event.pointerId);
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, time: performance.now() });
        yawVelocity = 0;
        pitchVelocity = 0;
        if (pointers.size === 2) pinchStart = { distance: pointerDistance(), fov: viewFov };
    });

    canvas.addEventListener("pointermove", (event) => {
        const previous = pointers.get(event.pointerId);
        if (!previous) return;
        const now = performance.now();
        if (pointers.size === 1) {
            const deltaX = event.clientX - previous.x;
            const deltaY = event.clientY - previous.y;
            const elapsed = Math.max(8, now - previous.time) / 1000;
            const yawDelta = -deltaX / Math.max(1, canvas.clientWidth) * horizontalViewFov();
            const pitchDelta = deltaY / Math.max(1, canvas.clientHeight) * viewFov;
            yaw = wrapAngle(yaw + yawDelta);
            pitch = Math.max(-55 * DEG, Math.min(45 * DEG, pitch + pitchDelta));
            yawVelocity = yawDelta / elapsed;
            pitchVelocity = pitchDelta / elapsed;
        }
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, time: now });
        if (pointers.size === 2 && pinchStart) {
            const distance = pointerDistance();
            if (distance > 0) {
                viewFov = Math.max(42 * DEG, Math.min(112 * DEG, pinchStart.fov * pinchStart.distance / distance));
            }
        }
    });

    function releasePointer(event) {
        pointers.delete(event.pointerId);
        if (pointers.size < 2) pinchStart = null;
    }

    canvas.addEventListener("pointerup", releasePointer);
    canvas.addEventListener("pointercancel", releasePointer);
    document.getElementById("btnWayonLive").addEventListener("click", window.startWayonLiveView);
    document.getElementById("btnWayonLiveClose").addEventListener("click", window.stopWayonLiveView);
    photoButton.addEventListener("click", capturePanoramaPhoto);
    clip10Button.addEventListener("click", () => requestClip(10));
    clip30Button.addEventListener("click", () => requestClip(30));
    playbackToggle.addEventListener("click", () => {
        if (!savedPlayback) return;
        if (savedPlayback.finished) {
            restartSavedPlayback();
            return;
        }
        if (savedPlayback.paused) {
            savedPlayback.startedAt = performance.now() - savedPlayback.positionMs;
            savedPlayback.paused = false;
            setStatus("저장 영상");
        } else {
            savedPlayback.positionMs = Math.min(savedPlayback.durationMs, performance.now() - savedPlayback.startedAt);
            savedPlayback.paused = true;
            setStatus("일시정지");
        }
        updatePlaybackUi();
    });
    document.getElementById("btnWayonLiveCenter").addEventListener("click", () => {
        yaw = 0;
        pitch = 0;
        viewFov = 78 * DEG;
        yawVelocity = 0;
        pitchVelocity = 0;
    });
    retry.addEventListener("click", () => {
        if (overlay.classList.contains("playback") && savedPlaybackRequest) {
            window.startWayonSavedClip(savedPlaybackRequest);
            return;
        }
        intentionalClose = true;
        sessionRequestPending = false;
        stopHeartbeat();
        clearStartupTimer();
        clearTimeout(reconnectTimer);
        socket?.close();
        socket = null;
        requestSession();
    });
    document.addEventListener("visibilitychange", () => {
        if (document.hidden && overlay.classList.contains("active")) window.stopWayonLiveView();
    });
    window.addEventListener("resize", resizeCanvas);

    setInterval(() => {
        if (!overlay.classList.contains("active")) return;
        const now = performance.now();
        const elapsed = now - fpsStartedAt;
        if (elapsed >= 1000) {
            measuredFps = Math.round(frameCounter * 1000 / elapsed / 2);
            frameCounter = 0;
            fpsStartedAt = now;
            if (status.classList.contains("live")) statusText.textContent = `LIVE · ${measuredFps} fps`;
        }
    }, 1000);
})();
