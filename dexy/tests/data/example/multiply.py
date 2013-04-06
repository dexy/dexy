### @export "assign-variables"
x = 6
y = 7

### @export "multiply"
print x*y


### @export "make-new-file"
with open("foo.txt", "w") as f:
    f.write("hello!")
