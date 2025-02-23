require 'sinatra'
require 'sinatra/reloader' if development?
require 'rtesseract'
require 'dotenv/load'
require 'redcarpet'
require 'json'

# Enable static files in the public folder
set :public_folder, File.dirname(__FILE__) + '/public'

# Initialize Markdown renderer
markdown = Redcarpet::Markdown.new(Redcarpet::Render::HTML, autolink: true, tables: true)

# Initialize a hash to store books
$books = {}

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
  book_name = params[:book_name]
  filename = params[:filename]
  note_name = params[:note_name]
  text = params[:text]

  # Initialize the book if it doesn't exist
  $books[book_name] ||= {}

  # Save the note to the book with its name and text
  $books[book_name][filename] = { name: note_name, text: text }

  redirect "/book/#{book_name}"
end

get '/books.json' do
  content_type :json
  $books.to_json
end

get '/books' do
  erb :books, locals: { books: $books }
end

get '/book/:book_name' do
  book_name = params[:book_name]
  book_notes = $books[book_name] || {}

  erb :book, locals: { book_name: book_name, notes: book_notes }
end

post '/highlight' do
  if params[:image] && params[:x] && params[:y] && params[:width] && params[:height]
    # Save the uploaded file
    file = params[:image][:tempfile]
    filename = params[:image][:filename]
    filepath = "./public/uploads/#{filename}"
    File.open(filepath, 'wb') do |f|
      f.write(file.read)
    end

    # Extract text from the highlighted area
    x = params[:x].to_i
    y = params[:y].to_i
    width = params[:width].to_i
    height = params[:height].to_i

    extracted_text = RTesseract.new(filepath, rect: [x, y, width, height]).to_s
    extracted_text
  else
    "No image or coordinates provided."
  end
end