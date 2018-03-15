from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify,make_response
import atexit
import cf_deployment_tracker
import os
import json
import swiftclient.client as swiftclient
from werkzeug.utils import secure_filename
import base64


# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

#Basic connection details
auth_url = "https://identity.open.softlayer.com/v3"
project = ""
projectId = ""
region = "dallas"
userId = ""
username = ""
password = ""
container_name = ''

#Path Details
Downloadpath = '/Downloads'
FOLDER_PATH= os.path.dirname(os.path.abspath(__file__))
Uploadpath='/home/vcap/app/'


#Cloud Connection Details
connectionst = swiftclient.Connection(
    key=password,
    authurl=auth_url,
    auth_version='3',
    os_options={"project_id": projectId,
                "user_id": userId,
                "region_name": region})

# Port Details
port = int(os.getenv('PORT', 8000))


#Home Page
@app.route('/')
def home():
    allFileDetails=[]
    # List objects in a container, and prints out each object name, the file size, and last modified date
    print ("nObject List:")
    for container in connectionst.get_account()[1]:
        for data in connectionst.get_container(container['name'])[1]:
            print('object: {0}t size: {1}t date: {2}'.format(data['name'], data['bytes'], data['last_modified']))
            allFileDetails.append(data)
    return render_template('index.html', result=container_name , result2=allFileDetails)

#upload File Operations
@app.route('/uploadfile',methods=['POST','GET'])
def uploader():
    if request.method == 'POST':
        file = request.files['fileName']
        filename = secure_filename(file.filename)
        file.save(os.path.join(Uploadpath , filename))
        # get File size - os.path.getsize(file_path)
       # os.remove() will remove a file.

        #os.rmdir() will remove an empty directory.

        #shutil.rmtree() will delete a directory and all its contents.

        with open(Uploadpath+'/'+filename, 'rb') as example_file:
            encryptingFile = base64.b64encode(example_file.read())
            connectionst.put_object(container_name, filename,
                                    contents= encryptingFile,
                                    content_type='text/plain')

        return render_template('index.html' , resultText="File Uploaded Successfully to Cloud/Bluemix")


#Download File Operations
@app.route('/downloadfile',methods=['POST','GET'])
def Downloader():
    if request.method == 'POST':
        filename = request.form['fileName']
        download = connectionst.get_object(container_name, filename)
        with open(filename, 'wb') as download_file:
            base64_decode = base64.b64decode(download[1])
            response = make_response(base64_decode)
            response.headers["Content-Disposition"] = "attachment; filename=%s" % filename
            download_file.write(base64_decode)
            download_file.close()
    #return render_template('index.html',resultText="File Downloaded Successfully from Cloud/Bluemix" )
    return response

#Delete File
@app.route('/deletefile',methods=['POST','GET'])
def DeleteFile():
    if request.method == 'POST':
        filename = request.form['fileName']
        connectionst.delete_object(container_name, filename)
    return render_template('index.html' , resultText="File deleted Successfully from Cloud/Bluemix")



#Main Function
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
