
from os import getenv
from requests import post
from random import randint

#%%
def send_df_as_flex(df, cols=['title', 'content'], text="info", color="RANDOM", size="xs", sort=False, msg_endpoint="XXX", reciever="cloud"):

    msg_list = [{"title": x[0], "content": x[1]} for x in df[cols].values]

    titles = set([x["title"] for x in msg_list])
    titles = sorted(list(titles)) if sort else list(titles)
    bubbles = []
    for t in titles:
        # color [#RRGGBB, #RRGGBBAA, AA, RANDOM]        
        title_color = f"#{randint(0,255):02X}{randint(0,255):02X}{randint(0,255):02X}" \
                if color == "RANDOM" or len(color) == 2 else color
        title_text_color = "#FFFFFF"
        
        if len(color) ==2:
            title_color = title_color + color
            title_text_color = "#999999"

        bubbles.append({
            "type": "bubble",
            "size": "micro",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": title_color,
                "contents": [{
                    "type": "text",
                    "text": str(t),
                    "size": "xxs",
                    "color": title_text_color,
                    "wrap": True
                }]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                        "type": "text",
                        "text": x["content"],
                        "size": size,
                        "color": "#aaaaaa",
                        "wrap": True
                    } for x in msg_list if x["title"]==t]
            }
        })

    flex_json = {"type": "carousel", "contents": bubbles}
    if len(msg_endpoint)>10:
        try:
            res = post(
                msg_endpoint,
                headers={"Authorization": f"Bearer {getenv('tokendata')}"},
                json = {"to": reciever, "text": text, "flex": flex_json}
            )
            # print(f"{res.status_code} {res.text}")                
        except Exception as e:
            # print(flex_json)
            print(f"failed to post line message due to {str(e)}")

    return flex_json