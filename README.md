# clockin
This is a clockin app python QT version. Use "requests" to communicate with backend server by calling API.

## UI design
I used Figma to desgin some simple ui pages.

Here is the link https://www.figma.com/file/uww1tfZv7DmERBS533Ljoq/%E6%89%93%E5%8D%A1app?node-id=0%3A1

You can follow those design forms to layout your app.

Click the right top present button,you will see a phone and you can click the buttons to see the motions. 

![](https://i.imgur.com/KRox8DR.png)


## python code
Because the lightcnn_weight model is too large, I put all the models on my Google drive.
https://drive.google.com/drive/folders/1yrxntoID7t4D04F3RRO6T1JdjkfP7LCH?usp=sharing

Download the weight/ folder and put it under the root directory.

Run the code 
```
python main.py
```
### main.py 

This is the main process. Each classes represents each ui pages.

All the variables are the names from each .ui files.
You can download QT desinger to check those variables.

![](https://i.imgur.com/t5oJuZC.png)

### face_recognize.py

face_recognize.py is a QThread .It start works when the main.py initialize.

It is used for identify the faces and regist the faces.
I used self.start_recognize to control it start or not.

## Call the API
Follow the platform below, send the datas to the backend sever.
Then you will receive the resonse from the sever.

example
```
host = "20.112.4.234:8080"
service = 'login'

send_dict = {}
send_dict['account'] = 'test3'
send_dict['password'] = 'testtest'
send_dict['mail'] = 'test3@gigabyte'
send_dict['third_party'] = 'None'

res = requests.post('http://%s/%s'%(host,service), data=send_dict)
response = json.loads(res.content.decode("utf-8"))
print(response)

```
