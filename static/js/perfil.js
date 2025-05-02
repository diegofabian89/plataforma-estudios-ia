document.addEventListener("DOMContentLoaded", function () {

    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        });
    }, 3500);

    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function () {
            const input = document.getElementById(this.dataset.target);
            const icon = this.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-unlock');

            } else {
                input.type = 'password';
                icon.classList.remove('fa-unlock');
                icon.classList.add('fa-eye');

            }
        });
    });

    const avatarSelect = document.getElementById("id_avatar_default");
    const avatarPreview = document.getElementById("avatar_preview");

    if (avatarSelect && avatarPreview) {
        avatarSelect.addEventListener("change", () => {
            const selectedAvatar = avatarSelect.value;
            if (selectedAvatar) {
                avatarPreview.src = `/static/img/avatars/${selectedAvatar}`;
            }
        });
    }

    const inputImagen = document.getElementById("id_imagen");
    if (inputImagen && avatarPreview) {
        inputImagen.addEventListener("change", function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
