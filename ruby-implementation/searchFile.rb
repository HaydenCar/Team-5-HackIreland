require 'find'

# List of files to search for
files_to_find = ['index.erb', 'result.erb', 'book.erb', 'books.erb', 'app.rb', 'Gemfile', 'styles.css']

# Search for files in the current directory and its subdirectories
Find.find('.') do |path|
  if File.file?(path) && files_to_find.include?(File.basename(path))
    puts "File: #{path}"
    puts "Content:"
    puts File.read(path)
    puts "-" * 40
  end
end
