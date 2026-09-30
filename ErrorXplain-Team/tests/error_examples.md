# 15 Real gcc/clang Error Examples — Expected Rule Mapping

Use these to test the engine (first matching rule wins, case-insensitive substring then regex).

### 1
Error message:
  `main.c:5:12: error: expected ';' before 'return'`
Expected rule:
  `c_missing_semicolon`

### 2
Error message:
  `main.c:3:10: error: use of undeclared identifier 'x'; did you mean 'y'?`
Expected rule:
  `c_undeclared_identifier`

### 3
Error message:
  `main.c:4:5: warning: implicit declaration of function 'printf' is invalid in C99 [-Wimplicit-function-declaration]`
Expected rule:
  `c_implicit_function_declaration`

### 4
Error message:
  `main.c:6:1: warning: control reaches end of non-void function [-Wreturn-type]`
Expected rule:
  `c_missing_return_value`

### 5
Error message:
  `Segmentation fault (core dumped)`
Expected rule:
  `c_segmentation_fault`

### 6
Error message:
  `main.c:7:5: error: too few arguments to function 'add'`
Expected rule:
  `c_too_few_arguments`

### 7
Error message:
  `main.c:8:3: error: too many arguments to function 'foo'`
Expected rule:
  `c_too_many_arguments`

### 8
Error message:
  `main.c:9:15: warning: passing argument 1 of 'printStr' from incompatible pointer type [-Wincompatible-pointer-types]`
Expected rule:
  `c_incompatible_pointer_type`

### 9
Error message:
  `main.c:10:14: warning: format '%d' expects argument of type 'int' but argument 2 has type 'char *' [-Wformat=]`
Expected rule:
  `c_format_string_mismatch`

### 10
Error message:
  `main.c:11:12: warning: 'count' is used uninitialized in this function [-Wuninitialized]`
Expected rule:
  `c_uninitialized_variable`

### 11
Error message:
  `main.c:12:7: error: assignment of read-only variable 'MAX'`
Expected rule:
  `c_assignment_to_const`

### 12
Error message:
  `main.c:6:5: error: break statement not within loop or switch`
Expected rule:
  `c_break_outside_loop`

### 13
Error message:
  `==123==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7fff5fbff123 at pc 0x55a123`
Expected rule:
  `c_array_out_of_bounds`

### 14
Error message:
  `free(): double free detected in tcache 2`
Expected rule:
  `c_double_free`

### 15
Error message:
  `main.c:9:1: error: expected '}' at end of input`
Expected rule:
  `c_missing_closing_brace`
