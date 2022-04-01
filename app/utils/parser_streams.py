def parser(stream_data):
    streams = stream_data[1]["data"]
    list_streams_on = [
        {
            "channel_name": x["user_name"],
            "game": x["game_name"],
            "viewers": x["viewer_count"],
            "channel_status": x["title"],
            "preview_img": x["thumbnail_url"].replace("-{width}x{height}", ""),
        }
        for x in streams
    ]
    return list_streams_on

# {
#       "id": "42170724654",
#       "user_id": "132954738",
#       "user_login": "aws",
#       "user_name": "AWS",
#       "game_id": "417752",
#       "game_name": "Talk Shows & Podcasts",
#       "type": "live",
#       "title": "AWS Howdy Partner! Y'all welcome ExtraHop to the show!",
#       "viewer_count": 20,
#       "started_at": "2021-03-31T20:57:26Z",
#       "language": "en",
#       "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/live_user_aws-{width}x{height}.jpg",
#       "tag_ids": [
#         "6ea6bca4-4712-4ab9-a906-e3336a9d8039"
#       ]
#     },