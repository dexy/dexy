library(tools)
library(rjson)

if (length(packages) == 0) {
    stop("no packages!")
}

# This function will do the real work of extracting content.  It should return
# a list of lists each with 2 entries, the section name and the content for
# that section. Many sections will just return 1 such list, but sometimes we
# will want to process a section in multiple ways, e.g. format hyperlinks for
# both HTML and LaTeX, so we expect to return a list of lists to account for
# this.
processSection <- function(content, tag) {
    result <- switch(tag,

                     "\\alias"=processSimple(content),
                     "\\arguments"=processArguments(content),
                     "\\author"=processSimple(content),
                     "\\description"=processSimple(content),
                     "\\details"=processSimple(content),
                     "\\examples"=processExamples(content),
                     "\\keyword"=processSimple(content),
                     "\\name"=processSimple(content),
                     "\\note"=processSimple(content),
                     "\\references"=processSimple(content),
                     "\\section"=processSubSection(content),
                     "\\seealso"=processSimple(content),
                     "\\source"=processSimple(content),
                     "\\title"=processSimple(content),
                     "\\usage"=processUsage(content),
                     "\\value"=processSimple(content),
                     "\\COMMENT"=processSimple(content),

                     # default case
                     stop(paste("I don't know how to handle tag '", tag, "'", sep=""))
                     )
    return(result)
}

stripLeadingTrailingWhitespace <- function(s) {
    s <- gsub('[[:space:]]+$', ' ', s)
    s <- gsub('^[[:space:]]+', ' ', s)
    return(s)
}

stripLeadingTrailingSpaceAbsolute <- function(s) {
    s <- gsub('[[:space:]]+$', '', s)
    s <- gsub('^[[:space:]]+', '', s)
    return(s)
}

fixDoubleSpaces <- function(s) {
    return(gsub('\\s+', ' ', s))
}

sep <- function() {
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
}

processSubSection <- function(content) {
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
    }
    return(list(list("section", "blah")))
}

processUsage <- function(content) {
    usage_content <- c()
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        if (item_tag %in% c("\\method", "\\S4method", "\\S3method")) {
            usage_content <- c(usage_content, item[[1]][[1]]) # dropping 2nd element, could also join with "."
        } else if (item_tag %in% c("RCODE", "\\dots")) {
            usage_content <- c(usage_content, item)
        } else {
            stop(paste("I don't know how to handle tag '", item_tag, "' in usage", sep=""))
        }
    }
    return(list(list("usage", stripLeadingTrailingWhitespace(paste(usage_content, sep="", collapse="")))))
}

processExamples <- function(content) {
    examples <- list()
    all_examples <- list()
    dontrun_examples <- list()

    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        example_content <- processExample(item)

        if (length(grep("^[[:space:]]*$", example_content)) > 0) {
            next # skip this blank line
        }

        if (item_tag %in% c("RCODE", "\\S4method", "\\method", "\\testonly")) {
            examples[[length(examples) + 1 ]] <- example_content
            all_examples[[length(all_examples) + 1 ]] <- example_content
        } else if (item_tag %in% c("\\dontrun", "\\donttest")) {
            dontrun_examples[[length(dontrun_examples) + 1 ]] <- example_content
            all_examples[[length(all_examples) + 1 ]] <- example_content
        } else {
            stop(paste("I don't know how to handle tag '", item_tag, "' in examples", sep=""))
        }
    }

    label <- "examples"
    return_examples <- list(label, examples)
    return_dontrun_examples <- list(paste(label, "dontrun", sep="-"), dontrun_examples)
    return_all_examples <- list(paste(label, "all", sep="-"), all_examples)
    return(list(return_examples, return_dontrun_examples, return_all_examples))
}

processExample <- function(content) {
    return(paste(content, sep="", collapse=""))
}

processArguments <- function(content) {
    arguments_list <- list()
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        result <- switch(item_tag,
                         TEXT=NA,
                         COMMENT=NA,
                         "\\item"=processArgument(item),

                         # default case
                         stop(paste("I don't know how to handle tag '", item_tag, "' in arguments"))
                         )

        if (!is.na(result)) {
            arguments_list[result[[1]]] <- result[[2]]
        }
    }
    return(list(list("arguments", arguments_list)))
}

processArgument <- function(content) {
    argument_name <- processSimpleChunk(content[[1]][[1]])
    argument_info <- stripLeadingTrailingSpaceAbsolute(paste(lapply(content[[-1]], processSimpleChunk, TRUE), sep="", collapse=""))
    return(list(argument_name, fixDoubleSpaces(argument_info)))
}

# Use this when we don't need any fancy processing.
processSimple <- function(content) {
    section_tag <- attr(content, "Rd_tag")
    clean_tag <- strsplit(section_tag, "\\", fixed=TRUE)[[1]][[2]]

    processedContent <- paste(lapply(content, processSimpleChunk), sep="", collapse="")
    basic_entry <- list(clean_tag, fixDoubleSpaces(processedContent))
    return(list(basic_entry))
}

# Checks to make sure the data type is appropriate for simple processing,
# returns the chunk's content unchanged.
processSimpleChunk <- function(chunk, stripExtraWhitespace=TRUE) {
    chunk_description <- attr(chunk, "Rd_tag")
    result <- switch(chunk_description,
                     "\\R"="R",
                     "\\S4method"=chunk,
                     "\\code"=chunk,
                     "\\command"=chunk,
                     "\\dQuote"=chunk,
                     "\\describe"=chunk,
                     "\\dots"=chunk,
                     "\\email"=chunk,
                     "\\emph"=chunk,
                     "\\enumerate"=chunk,
                     "\\env"=chunk,
                     "\\eqn"=chunk,
                     "\\file"=chunk,
                     "\\item"=chunk,
                     "\\itemize"=chunk,
                     "\\link"=chunk,
                     "\\method"=chunk,
                     "\\option"=chunk,
                     "\\pkg"=chunk,
                     "\\preformatted"=chunk,
                     "\\sQuote"=chunk,
                     "\\samp"=chunk,
                     "\\tabular"=chunk,
                     "\\url"=chunk,
                     "\\var"=chunk,
                     "\\verb"=chunk,
                     CODE=chunk,
                     COMMENT=chunk,
                     LIST=chunk,
                     RCODE=chunk,
                     TEXT=chunk,
                     VERB=chunk,

                     # default case
                     stop(paste("I don't know how to handle data type '", chunk_description, "'", sep=""))
                     )
    if (length(result) == 0) {
        result = ""
    }
    if (stripExtraWhitespace) {
        result <- stripLeadingTrailingWhitespace(result)
    }
    return(result)
}

# TODO check based on data.filename extension

if (grepl(".sqlite3", data.filename)) {
    cat("using sqlite")
    library(RSQLite)

    # Set up storage
    conn <- dbConnect(SQLite(), data.filename)
    dbSendQuery(conn, "CREATE TABLE kvstore (key TEXT, value TEXT)")
    dbBeginTransaction(conn)

    # Define append function
    append_kv <- function(key, value) {
        sql <- "INSERT INTO kvstore VALUES (:key, :value)"
        if (class(value) != "list") {
            dbGetPreparedQuery(conn, sql, bind.data = data.frame(key=key, value=value))
        } else {
            # json-encode the data first
            dbGetPreparedQuery(conn, sql, bind.data = data.frame(key=key, value=toJSON(value)))
        }
    }

    # Define persist/save function
    save_kv <- function() {
        dbCommit(conn)
        dbDisconnect(conn)
    }

} else if  (grepl(".json", data.filename)) {
    cat("using JSON")

    # Set up storage
    packages_info <- new.env(hash=TRUE)

    # Define append function
    append_kv <- function(key, value) {
        assign(key, value, env=packages_info)
    }

    # Define persist/save function
    save_kv <- function() {
        data_file <- file(data.filename, "w")
        writeLines(toJSON(as.list(packages_info)), data_file)
        close(data_file)
    }

} else {
    stop(data.filename)
}

# Main loop in which we gather content by iterating over packages, Rd files
# within packages and tags within Rd files.
for (pkg_name in packages) {
    # Load the package, so we can obtain source code from methods.
    require(pkg_name, character.only = TRUE, keep.source = TRUE)

    # Get the stored Rd files for this package.
    db <- Rd_db(pkg_name)

    # Pre-process each Rd chunk.
    Rd_list <- lapply(db, tools:::prepare_Rd)
    tags_list <- lapply(Rd_list, tools:::RdTags)

    # Get the canonical name for each Rd file.
    names <- lapply(db, tools:::.Rd_get_metadata, "name")

    for (f in names(db)) {
        # Get the data corresponding to this file.
        Rd <- Rd_list[[f]]
        tags <- tags_list[[f]]

        # Set up an environment for this file's info.
        file_info <- new.env(hash=TRUE)

        # Store the info we want in the environment.
        append_kv(paste(pkg_name, names[[f]], "filename", sep=":"), f)

        if (exists(names[[f]])) {
            f_closure <- get(names[[f]])
            source_code <- paste(deparse(f_closure), collapse="\n")
            append_kv(paste(pkg_name, names[[f]],  "source", sep=":"), source_code)
        }
        for (i in seq_along(tags)) {
            results <- processSection(Rd[[i]], tags[[i]])
            for (result in results) {
                append_kv(paste(pkg_name, names[[f]], result[[1]], sep=":"), result[[2]])
            }
        }
    }
    # Detach this package now that we are done with it.
    name_with_pkg <- paste("package", pkg_name, sep=":")
    detach(name_with_pkg, character.only = TRUE)
}

save_kv()
