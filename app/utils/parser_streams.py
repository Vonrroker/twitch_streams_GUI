def parser(stream_data):
    streams = stream_data[1]["streams"]
    list_streams_on = [
        {
            "channel_name": x["channel"]["name"],
            "game": x["game"],
            "viewers": x["viewers"],
            "channel_status": x["channel"]["status"],
            "preview_img": x["preview"]["large"],
        }
        for x in streams
    ]
    return list_streams_on
