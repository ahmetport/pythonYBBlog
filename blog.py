from flask import Flask ,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullanıcı giriş decaratoru
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("bu sayfaya gitmek için giriş yapmalısınız...","danger")
            return redirect(url_for("login"))    
    return decorated_function


# kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("isim soyisim",validators=[validators.Length(min=4,max=25)])
    username = StringField("kullanici adi",validators=[validators.Length(min=5,max=30)])
    email = StringField("email adresi",validators=[validators.Email(message = "lütfen geçerli email giriniz...")])
    password=PasswordField("paralo:", validators=[
        validators.DataRequired(message = "lutfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm", message = "paralonuz dogrulanmıyor tekrar deneyin")
    ])
    confirm=PasswordField("parolayı dogrulayınız...")
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")    
    

app= Flask(__name__)
app.secret_key="ybblog"  # flash mesajlarını kullanabilmek için kendi kafamdan bi tane secret key oluşturuyoruz
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


Mysql=MySQL(app)

@app.route("/")
def index():
    return render_template("index.html" , answer = "2")

@app.route('/about')
def about():
    return render_template("about.html")

# makale sayfası
@app.route('/articles')
def articles():
    cursor=Mysql.connection.cursor()
    sorgu="Select * from articles"
    result=cursor.execute(sorgu)

    if result > 0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

#kontrol paneli 
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=Mysql.connection.cursor()
    sorgu="Select * from articles where author = %s"
    result=cursor.execute(sorgu,(session ["username"],))

    if result > 0 :
        articles= cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
       return render_template("dashboard.html")

# kayıt olma
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method =="POST" and form.validate():
        name = form.name.data
        username =form.username.data
        email= form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=Mysql.connection.cursor()
        sorgu="Insert into users(name,username,email,password) VALUES (%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        Mysql.connection.commit() # guncelleme yapmak için commiti mutlaka yapmamız lazım
        cursor.close()  # arka taraf bosuna çalışmasın diye

        flash("Başarıyla kayıt oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form) 


#@app.route("/article/<string:id>")
#def detail(id):
#    return "article Id :" + id

# Login işlemi burdan başlıyor
@app.route("/login",methods = ["GET","POST"]) 
def login():
    form=LoginForm(request.form)
    if request.method == "POST": # reguest post ise
        username = form.username.data # datalarımı oluşturdum
        password_entered = form.password.data

        cursor = Mysql.connection.cursor() # cursor ile baglantı yap
        sorgu = "Select * From users where username = %s" # username sorgusunu veri tabanından iste
        result = cursor.execute(sorgu,(username,)) # burda sorguyu çalıştırıyoruz boyle bir username var mı diye

        if result > 0 :
            data = cursor.fetchone() # users dataları alsın isim e mail password username
            real_password = data["password"] # password istesin veri tabanındakini
            if sha256_crypt.verify(password_entered,real_password):#girilen password ile veri tabanındakını dogrulasın
                flash("Başarılı Giriş Yaptınız...","success") # mesaj caksin

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index")) # tekrar index sayfasına ana sayfaya gitsin
            else:
                flash("Parolanız Yanlış Girdiniz...","danger")
                return redirect(url_for("login")) 
        else:
            flash("Böyle bir Kullanici Bulunmuyor...","danger")
            return redirect(url_for("login"))
    
        
    return render_template("login.html",form=form)

# Detay sayfası
@app.route("/article/<string:id>")   
def article(id):
    cursor=Mysql.connection.cursor()
    sorgu="Select * from articles where id = %s"
    result=cursor.execute(sorgu,(id,)) 

    if result > 0:
        article=cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")
#LoGOUT İŞLEMİ    
@app.route("/logout")
def lagout():
    session.clear()
    return redirect(url_for("index"))
# makale ekleme
@app.route("/addarticle", methods= ["GET", "POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content=form.content.data

        cursor= Mysql.connection.cursor()
        sorgu = "insert into articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        cursor.connection.commit()
        cursor.close()
        flash("Makale Başarı ile eklendi...","success")
        return redirect(url_for("dashboard")) 


    return render_template("addarticle.html",form=form) 
# makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=Mysql.connection.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))

    if result > 0 :
        sorgu2="Delete  from articles where id =%s "
        cursor.execute(sorgu2,(id),)
        Mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya yetkiniz yok")
        return redirect(url_for("index")) 


# makale güncelle
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def uptade(id):
    if request.method == "GET":
        cursor = Mysql.connection.cursor()
        sorgu = "Select * from articles where id =%s and author =%s"
        result = cursor.execute(sorgu,(id,session["username"])) 

        if result == 0:
            flash("böyle bir makale yok veya yetkiniz yok")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm() 

            form.title.data= article["title"]
            form.content.data=article["content"]
            return render_template("update.html", form=form)
    else:
  #post request kısmı
        form=ArticleForm(request.form)
        newtitle = form.title.data
        newcontent= form.content.data

        sorgu2="update articles set title=%s,content = %s where id =%s"
        cursor=Mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))  
        Mysql.connection.commit()

        flash("makale başarıyla guncellendi", "success")
        return redirect(url_for("dashboard"))               





# makale form
class ArticleForm(Form):
    title=StringField("Makale Başlıgı",validators=[validators.length(min=5 ,max =100)])
    content=TextAreaField("Makale İçerigi",validators=[validators.length(min=10)])

#arama url
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method =="GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor= Mysql.connection.cursor()
        sorgu= "Select * from articles where title like '%" + keyword +"%'" 
        result = cursor.execute(sorgu)

        if result == 0 :
            flash("Arana kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles")) 
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)      

if __name__ == "__main__":
    app.run(debug=True)
