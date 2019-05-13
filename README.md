# TheCatalogApp

This application provides the details of items belonging to a certail sports categories,
with a third party(Google) user authentication system. Where the user will have the capability to
Add Items and Edit and delete their own items.


#### 1. System set-up

* Download Unix style terminal [Git Bash](https://git-scm.com/downloads)
* Download the [Virtual Box](https://www.virtualbox.org/wiki/Downloads)
* Download [Vagrant Machine](https://www.vagrantup.com/downloads.html)



#### 2. Run the virtual machine!

commands to run vagrant machine

```
vagrant up
vagrant ssh

```

#### 3.Move downloaded git inside the vagrant directory

 run the following command
 
 Below commmands imports the Catalog raw data and sets up the detabase for the project
 
```
python databaseSetup.py
python CatalogData.py
```
After the above commands run the python project.

```
python project.py

```
#### 4. Load the application in the browser at (http://localhost:5000)

#### 5. Manual to use the application.

* Before login the main page has the list of categories and Items.
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/main_page.png)

* If there is no user session , clicking on Item will go to Item description page.
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/ItemDescription.png)

* clinking on each categories will list out the Items in that particular category
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/CategoryList.png)

* Login via google using the Sign in button in the Right botton corner of the page.
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/main_page_2.png)

* Post successfull login, the Add Item link appear on the mail screen which can be used to add new Item
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/MainPagePostLogin.png)

* Post successfull login, clicking on the Items links will lead to the Item detail page with a Edit or Delete option
* The Edit and Delete for a Particular Item will work only if the Item was created by the user crrently logged in.
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/ItemDescriptionPostLogin.png)

* Logout button available on the home page (home Icon avaiable on the left top corner of the page), can be logged out 
as the current user session.
![Screeshot](https://github.com/Shreya957/TheCatalogApp/blob/master/image/logout.png)

