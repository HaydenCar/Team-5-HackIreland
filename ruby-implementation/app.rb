require 'sinatra'
require 'sinatra/reloader' if development?
require 'rtesseract'
require 'dotenv/load'
require 'redcarpet'
require 'mongo'

# Enable static files in the public folder
set :public_folder, File.dirname(__FILE__) + '/public'

# Initialize Markdown renderer
markdown = Redcarpet::Markdown.new(Redcarpet::Render::HTML, autolink: true, tables: true)

# Set up MongoDB connection
Mongo::Logger.logger.level = ::Logger::WARN
# Use the MONGODB_URI environment variable and specify a database name (e.g., 'notes_app')
client = Mongo::Client.new(ENV['MONGODB_URI'], database: 'notes_app')
notes_collection = client[:notes]

get '/' do
  erb :index
end

post '/upload' do
  if params[:image] && params[:image][:filename]
    # Save the uploaded file
    filename = params[:image][:filename]
    file = params[:image][:tempfile]
    filepath = "./public/uploads/#{filename}"
    File.open(filepath, 'wb') do |f|
      f.write(file.read)
    end

    # Extract text using Tesseract
    extracted_text = RTesseract.new(filepath).to_s

    # Call the Python script to clean up the text
    cleaned_text = `python3 openai_cleanup.py "#{extracted_text.gsub('"', '\"')}"`

    # Convert markdown to HTML
    html_content = markdown.render(cleaned_text)

    # Render the result page with cleaned-up text
    erb :result, locals: { text: html_content, filename: filename }
  else
    "No image selected. <a href='/'>Go back</a>"
  end
end

post '/save_note' do
  note = {
    book_name: params[:book_name],
    filename: params[:filename],
    note_name: params[:note_name],
    text: params[:text],
    created_at: Time.now
  }

  # Insert the note into MongoDB
  notes_collection.insert_one(note)

  redirect "/book/#{params[:book_name]}"
end

get '/books' do
  # Get a distinct list of book names from the collection
  book_names = notes_collection.distinct("book_name")
  erb :books, locals: { books: book_names }
end

get '/book/:book_name' do
  book_name = params[:book_name]
  # Find all notes associated with the given book name
  book_notes = notes_collection.find({ book_name: book_name }).to_a

  erb :book, locals: { book_name: book_name, notes: book_notes }
end
