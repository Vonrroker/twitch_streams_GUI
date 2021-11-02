from app.config import envs

app_path = envs["app_path"]

fake_list_streams = [
    {
        "game": f"Nome do Jogo_{s}",
        "viewers": 000,
        "preview_img": f"{app_path}/tests/fakes/fake_preview.jpg",
        "channel_name": f"Name_{s}",
        "channel_status": "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. ",
    }
    for s in range(60)
]
