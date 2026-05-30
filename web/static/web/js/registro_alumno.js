/* ═══════════════════════════════════════════════════════════
   REGISTRO_ALUMNO.JS — Newton en Red
   Validación unificada: reemplaza el globito nativo del browser
   con mensajes .reg-error consistentes con el diseño del proyecto.
   Se aplica a todos los formularios dentro de .reg-card
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // Sube por el DOM hasta encontrar el .reg-field contenedor
    function campoContenedor(input) {
        var el = input.parentNode;
        while (el && !el.classList.contains('reg-field')) {
            el = el.parentNode;
        }
        return el || input.parentNode;
    }

    // Muestra un error frontend (.fe) bajo el campo
    function mostrarError(input, msg) {
        var contenedor = campoContenedor(input);
        // Elimina cualquier error anterior (frontend o backend)
        contenedor.querySelectorAll('.reg-error').forEach(function (el) { el.remove(); });
        input.classList.add('is-invalid');
        var span = document.createElement('span');
        span.className = 'reg-error fe';
        span.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + msg;
        contenedor.appendChild(span);
    }

    // Limpia el error cuando el usuario empieza a corregir el campo
    function limpiarError(input) {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        var contenedor = campoContenedor(input);
        contenedor.querySelectorAll('.reg-error').forEach(function (el) { el.remove(); });
    }

    // Aplica a todos los campos dentro de formularios de registro
    document.querySelectorAll('.reg-card form .reg-field input, .reg-card form .reg-field select').forEach(function (input) {

        // Intercepta el evento invalid — reemplaza globito por HTML
        input.addEventListener('invalid', function (e) {
            e.preventDefault();
            mostrarError(this, this.validationMessage);
        });

        // Limpia el error al escribir
        input.addEventListener('input', function () {
            limpiarError(this);
        });

        // Limpia el error al cambiar un select
        input.addEventListener('change', function () {
            limpiarError(this);
        });

    });

});
