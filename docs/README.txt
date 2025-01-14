# iSanXoT wiki

# Instructions for the updating documentation

1. Save the User Guide Word document (docs/user_guides/User_Guide_iSanXoT-X.X.X.docx) as HTML (Web Page, Filtered) into the iSanXoT help section (**iSanXoT/app/app/sections/help**).
    1.1. Important!! Save as 'UTF-8' encoding.
    1.2. Add into the 'User_Guide.htm' at the begining the tags:
    ```
    <template class="task-template" id="User_Guide">
    <html>
    <head>
    <base href="sections/help/">
    ```
    1.3. Add at the end the tags:
    </template>


2. Save the User Guide Word document (docs/user_guides/User_Guide_iSanXoT-X.X.X.docx) as HTML (Web Page, Filtered) into the iSanXoT help section (**iSanXoT/docs**).
    1.1. Important!! Save as 'UTF-8' encoding.
    1.2. Save into the 'index.htm'


3. Execute the following command:
    ```
    python transform_index.py index.htm index.html
    ```
