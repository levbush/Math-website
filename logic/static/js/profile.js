function showColorPalette() {
    document.getElementById('colorPalette').style.display = 'grid';
    document.getElementById('overlay').style.display = 'block';
}

function hideColorPalette() {
    document.getElementById('colorPalette').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function changeAvatarColor(color) {
    const avatarEl = document.getElementById('avatar');
    avatarEl.style.backgroundColor = color;
    avatarEl.className = 'avatar';
    avatarEl.innerHTML = '{{ current_user.username[:2].upper() }}';

    fetch('/user/update_avatar_color', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({color: color})
    }).then(r => r.json()).then(data => {
        if (data.status === 'ok') {
            fetch('/user/clear_avatar', {method: 'POST'});
            hideColorPalette();
        }
    });
}

function uploadAvatar(input) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('avatar', file);
    fetch('/user/upload_avatar', {method: 'POST', body: formData})
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                const avatarEl = document.getElementById('avatar');
                avatarEl.className = 'avatar avatar-img';
                avatarEl.innerHTML = '<img id="avatar-img-el" src="' + data.data_url + '" alt="avatar">';
                hideColorPalette();
            } else {
                alert(data.error || 'Upload failed.');
            }
        });
}

function clearAvatar() {
    fetch('/user/clear_avatar', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                location.reload();
            }
        });
}