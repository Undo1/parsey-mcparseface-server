contents = ""

ARGF.each do |line|
    if line.split(" ").join(" ").length > 0 
      contents << line
    else
      break
    end 
end

def print_word_dependencies(parents, parse)
  dependent_words = parse.scan(/^(\d*)\s*(\w*)\s*\w*\s*(\w*)\s*(\w*)\s*.\s*#{parents.last[0]}\s*(\w*)\s*\w*\s*\w*$/i)
  dependent_words.each do |dependent_word|
    out = "\n"
    parents.each do |parent|
      out = out + parent[1].downcase + " " # + parent[2] + " "
    end 
    out = out + dependent_word[1].downcase + " " # + dependent_word[2]

    if parse.scan(/^(\d*)\s*(\w*)\s*\w*\s*(\w*)\s*(\w*)\s*.\s*#{dependent_word[0]}\s*(\w*)\s*\w*\s*\w*$/i).count == 0 # if no children
      @output = @output + out
    end

    print_word_dependencies(parents + [dependent_word], parse)
  end 
end

parses = contents.split("\n\n")

@output = ""

parses.each do |parse|
  begin
    root = parse.scan(/^(\d*)\s*(.*?)\s*\w*\s*(\w*)\s*(\w*)\s*.\s*\d+\s*(root)/i).first
    print_word_dependencies([root], parse)
  rescue Exception => e
    puts e
  end 
end 

puts @output
puts "FINISHED"
