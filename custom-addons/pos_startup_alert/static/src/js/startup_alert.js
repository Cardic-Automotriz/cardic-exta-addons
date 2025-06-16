/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

// 1. Definimos la lógica de nuestro nuevo componente de botón
export class ConsoleLogButton extends Component {
    static template = "pos_startup_alert.ConsoleLogButton";

    setup() {
        this.pos = usePos();
    }

    onClick() {
        // ¡Esta es la acción que se ejecuta al hacer clic!

        // 1. Imprimimos en la consola
        console.log("¡ÉXITO! El botón de prueba funciona correctamente.");
        console.log("Puedes inspeccionar el estado del POS aquí:", this.pos);

        // 2. Mostramos un popup para confirmación visual inmediata
        this.pos.show_popup("ConfirmPopup", {
            title: "¡Funciona!",
            body: "El botón de prueba se ha ejecutado. Revisa la consola del navegador (F12) para ver más detalles.",
        });
    }
}

// 2. Usamos el método oficial de Odoo para añadir nuestro botón
// a la barra de botones de la pantalla de productos.
ProductScreen.addControlButton({
    component: ConsoleLogButton,
    position: ["before", "SetFiscalPositionButton"], // Lo posiciona al lado de otro botón existente
});