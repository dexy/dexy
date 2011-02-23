require 'java'

include_class 'java.util.TreeSet'
set = TreeSet.new
set.add "foo"
set.add "Bar"
set.add "baz"
set.each do |v|
  puts "value: #{v}"
end
