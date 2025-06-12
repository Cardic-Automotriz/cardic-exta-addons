odoo.define('rekognition_attendance.camera', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var registry = require('web.field_registry');
    var FormController = require('web.FormController');

    var QWeb = core.qweb;
    var _t = core._t;

    FormController.include({
        _onButtonClicked: function (ev) {
            if (ev.data.attrs.name === 'snap_photo') {
                this._takePhoto();
                return;
            }
            return this._super.apply(this, arguments);
        },

        _takePhoto: function () {
            var video = document.getElementById('video');
            var canvas = document.getElementById('canvas');
            var photo = document.getElementById('photo_result');
            var context = canvas.getContext('2d');

            // Dibuja la imagen del video en el canvas
            context.drawImage(video, 0, 0, 320, 240);

            // Convierte el canvas a base64
            var data = canvas.toDataURL('image/jpeg');
            photo.setAttribute('src', data);

            // Muestra la foto tomada y oculta el video
            document.getElementById('camera_block').style.display = 'none';
            document.getElementById('image_block').style.display = 'block';

            // Guarda la imagen en el campo binario
            this.model.set('image', data);
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(function (stream) {
                            var video = document.getElementById('video');
                            if (video) {
                                video.srcObject = stream;
                            }
                        })
                        .catch(function (err) {
                            console.log("Error al acceder a la cámara: " + err);
                        });
                }
            });
        },
    });
}); 