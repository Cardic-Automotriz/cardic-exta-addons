odoo.define('rekognition_attendance.camera', [], function (require) {
    'use strict';

    const { Component, useRef, onMounted, onWillUnmount } = require("@odoo/owl");
    const { useService } = require("@web/core/utils/hooks");
    const { _t } = require("@web/core/l10n/translation");

    class CameraComponent extends Component {
        setup() {
            this.videoRef = useRef('video');
            this.canvasRef = useRef('canvas');
            this.photoRef = useRef('photo');
            this.cameraBlockRef = useRef('camera_block');
            this.imageBlockRef = useRef('image_block');
            
            this.orm = useService("orm");
            this.notification = useService("notification");
            this.action = useService("action");
            
            this.stream = null;
            
            onMounted(() => this.startCamera());
            onWillUnmount(() => this.stopCamera());
        }

        async startCamera() {
            try {
                this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
                this.videoRef.el.srcObject = this.stream;
                await this.videoRef.el.play();
            } catch (err) {
                console.error("Error accessing camera:", err);
                this.notification.add(_t("Error"), {
                    type: "danger",
                    message: _t("Could not access camera: ") + err.message,
                });
            }
        }

        stopCamera() {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
        }

        async takePhoto() {
            const video = this.videoRef.el;
            const canvas = this.canvasRef.el;
            const photo = this.photoRef.el;
            const context = canvas.getContext('2d');

            context.drawImage(video, 0, 0, 320, 240);

            const data = canvas.toDataURL('image/jpeg').split(',')[1];

            photo.src = 'data:image/jpeg;base64,' + data;

            this.cameraBlockRef.el.style.display = 'none';
            this.imageBlockRef.el.style.display = 'block';

            try {
                await this.orm.write('rekognition.attendance.chekador', [this.props.recordId], {
                    image: data
                });

                const result = await this.orm.call(
                    'rekognition.attendance.chekador',
                    'action_check_attendance',
                    [this.props.recordId]
                );

                if (result && result.type === 'ir.actions.client') {
                    await this.action.doAction(result);
                }
            } catch (error) {
                this.notification.add(_t("Error"), {
                    type: "danger",
                    message: _t("Error processing image: ") + error.message,
                });
            }
        }

        retakePhoto() {
            this.cameraBlockRef.el.style.display = 'block';
            this.imageBlockRef.el.style.display = 'none';
        }
    }

    CameraComponent.template = 'rekognition_attendance.CameraComponent';
    CameraComponent.props = {
        recordId: { type: Number },
    };

    return CameraComponent;
});

odoo.define('rekognition_attendance.camera_mount', [], function (require) {
    'use strict';
    const { mount } = require('@odoo/owl');
    const CameraComponent = require('rekognition_attendance.camera').CameraComponent;

    function getRecordId() {
        const input = document.querySelector('.record_id_field input');
        if (input) {
            return parseInt(input.value, 10);
        }
        return null;
    }

    function mountCamera() {
        const cameraDiv = document.getElementById('camera_component');
        const recordId = getRecordId();
        if (cameraDiv && recordId) {
            mount(CameraComponent, { recordId: recordId }, { target: cameraDiv });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountCamera);
    } else {
        mountCamera();
    }
});
