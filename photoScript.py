# Import the requests module for send a PUT request
import requests
# Import the base64 module for encoding a file to base64
import base64


f=open('access.txt')
lines=f.readlines()


#githubAPIURL = "https://api.github.com/repos/fmalrs/23042prototype/contents/graph.png"
githubAPIURL = lines[5]

# Replace "bracketcounters" with your username, replace "test-repo" with your repository name and replace "new-image.png" with the filename you want to upload from local to GitHub.

# change access.txt to update github access file
#with open('access.txt', 'r') as file:
#    githubToken = file.read()
    
githubToken = lines[1]


with open("graph.png", "rb") as f:
    # Encoding "my-local-image.jpg" to base64 format
    encodedData = base64.b64encode(f.read())

    headers = {
        "Authorization": f'''Bearer {githubToken}''',
        "Content-type": "application/vnd.github+json"
    }
    data = {
        "message": "My commit message", # Put your commit message here.
        "content": encodedData.decode("utf-8")
    }

    r = requests.put(githubAPIURL, headers=headers, json=data)
    print(r.text) # Printing the response
                    
