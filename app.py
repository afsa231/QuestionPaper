from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError


app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['years']
tagged_collection = db['tagged_databases']

# Initialize tagged_databases set with existing data from the collection
tagged_databases = set(tagged_collection.distinct('database'))

@app.route('/')
def home():
    return render_template('paper.html')

@app.route('/yearcollections')
def get_collections():
    collections = db.list_collection_names()
    
    # Exclude specific collection 'tagged_databases' from the list of collections
    collections = [coll for coll in collections if coll != 'tagged_databases']
    
    return jsonify(collections)

@app.route('/attachdatabases')
def get_databases():
    databases = client.list_database_names()
    
    # Exclude system databases and other MongoDB internal databases
    available_databases = [db for db in databases if db != 'admin' and db != 'config' and db != 'local' and db != 'years' and db!='jabi']

    # Exclude tagged databases from the list of available databases
    available_databases = [db for db in available_databases if db not in tagged_databases]

    return jsonify(available_databases)

@app.route('/save-mapping', methods=['POST'])
def save_mapping():
    data = request.json
    collection_name = data.get('collection')
    selected_databases = data.get('databases')

    try:
        # Check if any selected database is already tagged
        if any(db in tagged_databases for db in selected_databases):
            return jsonify({'success': False, 'message': 'One or more selected databases are already tagged with a collection.'})

        # Insert the mapping information as a document in the selected collection
        selected_collection = db[collection_name]
        mapping_data = {
            'database': selected_databases,
            'collection_name': collection_name
        }
        selected_collection.insert_one(mapping_data)

        # Update the set of tagged databases
        tagged_databases.update(selected_databases)

        # Update the 'tagged_databases' collection with the new set of tagged databases
        tagged_collection.replace_one({}, {'database': list(tagged_databases)}, upsert=True)

        return jsonify({'success': True, 'message': 'Mapping saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# Collage selection
dbcol = client['collage']
collagename_collection = dbcol['collagename']
branchname_collection = dbcol['branchname']

@app.route('/get_collagenames', methods=['GET'])
def get_collagenames():
    # Retrieve data from the MongoDB collection
    collagenames = collagename_collection.distinct("data")  # Use the correct field name
    
    # Return the data as JSON
    return jsonify(collagenames)

@app.route('/get_branchnames', methods=['GET'])
def get_branchnames():
    branchnames = branchname_collection.distinct("data")
    
    return jsonify(branchnames)

# Years
@app.route('/get_years', methods=['GET'])
def get_years():
    # Retrieve data from the MongoDB "years" collection
    years = db.list_collection_names()
    
    # Exclude specific collection 'tagged_databases' from the list of collections
    years = [year for year in years if year != 'tagged_databases']
    
    return jsonify(years)



@app.route('/get_allcolection', methods=['GET'])
def gets():
    selected_subject = request.args.get('subject')

    # Check if the database exists for the selected subject
    if selected_subject in client.list_database_names():
        # Fetch collections from the selected database
        collections = client[selected_subject].list_collection_names()
        print(f"Selected Subject: {selected_subject}")
        print(f"Collections: {collections}")
        return jsonify(collections)
    else:
        print(f"No database found for the subject: {selected_subject}")
        return jsonify([])
    
#semester
@app.route('/get_semesters', methods=['GET'])
def get_semesters():
    selected_year = request.args.get('year')

    # Fetch semesters from the selected collection (year)
    semesters = db[selected_year].distinct("semester")  # Replace "semester" with the correct field name

    # Return the data as JSON
    return jsonify(semesters)

@app.route('/get_subjects', methods=['GET'])
def get_subjects():
    # Get the selected year and semester from the request parameters
    selected_year = request.args.get('year')
    selected_semester = request.args.get('semester')

    # Fetch documents from the selected collection (year and semester)
    subjects = db[selected_year].find({"semester": selected_semester}, {"database": 1, "_id": 0})

    # Extract the "database" field from each document
    database_fields = [item for sublist in [subject.get("database", []) for subject in subjects] for item in sublist]

    # Return the data as JSON
    return jsonify(database_fields)

import logging

logging.basicConfig(level=logging.DEBUG)

@app.route('/get_documents', methods=['GET'])
def get_documents():
    try:
        selected_subject = request.args.get('subject')
        selected_collection = request.args.get('collection')

        if not selected_subject or not selected_collection:
            return jsonify({'error': 'Subject and collection parameters are required'}), 400

        if selected_subject not in client.list_database_names():
            return jsonify({'error': f'Database not found for the subject: {selected_subject}'}), 404

        if selected_collection not in client[selected_subject].list_collection_names():
            return jsonify({'error': f'Collection not found in the database: {selected_collection}'}), 404

        cursor = client[selected_subject][selected_collection].find({})

        documents = [document for document in cursor]
        document_fields = [document.get("data", "") for document in documents]

        return jsonify({'documents': document_fields}), 200
    except PyMongoError as e:
        logging.error(f"MongoDB error: {str(e)}")
        return jsonify({'error': f'MongoDB error: {str(e)}'}), 500
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/insertpaper', methods=['POST'])
def insertpaper():
    # Retrieving data from the form
    code = request.form['code']
    regulation = request.form['regulation']
    rollno = request.form['rollno']
    colname = request.form['colname']
    colstatus = request.form['colstatus']
    newstatus = request.form.get('newstatus', '')
    yos=request.form['yos']
    tyofdg = request.form['tyofdg']
    tyofexam = request.form['tyofexam']
    monyr=request.form['monyr']
    yr = request.form['yr']
    sem = request.form['sem']
    subject = request.form['subject']
    branch = request.form['branch']
    time = request.form['time']
    marks = request.form['marks']
    opins1 = request.form['op1ins']
    opins2 = request.form['op2ins']
    romanmarks = request.form['romanmarks']
    collectionname = request.form['collectionname']
    selected_documents = request.form.getlist('documents[]')

    cdb=client['final']
    # Inserting data into MongoDB collection
    collect = cdb['mainpap']  # Assuming 'final' is your collection name
    data = {
        'code': code,
        'regulation': regulation,
        'rollno': rollno,
        'colname': colname,
        'colstatus': colstatus,
        'newstatus': newstatus,
        'yos':yos,
        'tyofdg': tyofdg,
        'tyofexam': tyofexam,
        'monyr':monyr,
        'yr': yr,
        'sem': sem,
        'subject': subject,
        'branch': branch,
        'time': time,
        'marks': marks,
        'opins1': opins1,
        'opins2': opins2,
        'romanmarks': romanmarks,
        'collectionname': collectionname,
        'selected_documents': selected_documents
    }
    collect.insert_one(data)

    # Printing for debugging purposes
    print(data)

    return render_template('paper.html')

    
@app.route('/submit_documents', methods=['POST'])
def submit_documents():
    # Retrieve the list of selected checkbox values
    selected_documents = request.form.getlist('documents[]')


    # Now you have the list of selected document indices (or values) in selected_documents
    print("Selected documents:", selected_documents)


@app.route('/showpapers')
def show_papers():
    # Connect to MongoDB and select the collection
    cdb = client['final']
    collect = cdb['mainpap']

    # Fetch all documents from the collection
    papers = collect.find()

    # Pass the data to the HTML template
    return render_template('showpap.html', papers=papers)



if __name__ == '__main__':
    app.run(debug=True)
