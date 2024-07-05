import vonage
client = vonage.Client(key="ea46d8f3", secret="3OxjaLLNc1WVF6f2")
sms = vonage.Sms(client)

responseData = sms.send_message(
    {
        "from": "Vonage APIs",
        "to": "233550545381",
        "text": "Kriss we are testing again",
    }
)

if responseData["messages"][0]["status"] == "0":
    print("Message sent successfully.")
else:
    print(f"Message failed with error: {responseData['messages'][0]['error-text']}")