function categoryEdit(id) {
    let name = document.getElementById("text" + id).value;
    // POSTで送る場合（FormData形式）
    fetch('/category_update', {
            method: 'POST',
            body: `id=${id}&name=${name}`,
            headers: new Headers({
                'Content-type': 'application/x-www-form-urlencoded'
            })
        })
        .then(response => response.text())
        .then(text => {
            if (text == "ok") {
                alert("更新しました");
            } else {
                alert("失敗しました");
            }
        });
}

function categoryDel(id) {
    let ok = window.confirm("削除しますか？");
    if (ok) {
        fetch('/category_delete', {
                method: 'POST',
                body: `id=${id}`,
                headers: new Headers({
                    'Content-type': 'application/x-www-form-urlencoded'
                })
            })
            .then(response => response.text())
            .then(text => {
                if (text == "ok") {
                    alert("削除しました");
                    location.href = "/category";
                } else {
                    alert("失敗しました");
                }
            });

    }
}