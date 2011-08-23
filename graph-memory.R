data <- read.table("memory.log", header=TRUE, sep="\t")

max_value = max(data$gc_count, data$vm_size)
pdf("memory-graph.pdf")
plot(data$timestamp, data$gc_count, type="l", ylim=c(0, max_value))
points(data$timestamp, data$vm_size, type="l", col="purple")
dev.off()

