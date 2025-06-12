odoo.define('rekognition_attendance.camera', function (require) {
    var FormController = require('web.FormController');
    var core = require('web.core');
    var qweb = core.qweb;
    
    FormController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === 'rekognition.attendance.chekador') {
                var video = document.getElementById('video');
                var canvas = document.getElementById('canvas');
                var snap = document.getElementById('snap');
                var cameraBlock = document.getElementById('camera_block');
                var imageBlock = document.getElementById('image_block');
                var photoResult = document.getElementById('photo_result');
                if (video && snap) {
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(function(stream) {
                            video.srcObject = stream;
                            video.play();
                        });
                    snap.onclick = function() {
                        canvas.getContext('2d').drawImage(video, 0, 0, 320, 240);
                        var dataURL = canvas.toDataURL('image/png');
                        // Quitar el encabezado y dejar solo el base64
                        var base64 = dataURL.replace(/^data:image\/png;base64,/, "");
                        // Llenar el campo invisible de imagen
                        var input = document.querySelector('input[name="image"]');
                        if (input) {
                            input.value = base64;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        // Ocultar cámara y mostrar imagen
                        if (cameraBlock && imageBlock && photoResult) {
                            cameraBlock.style.display = 'none';
                            imageBlock.style.display = 'block';
                            photoResult.src = dataURL;
                        }
                    };
                }
            }
        },
    });
}); 