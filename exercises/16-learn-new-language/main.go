// Mini-project for Exercise 16: a small word-frequency CLI in Go.
//
// Target language: Go (source language: Python). This demonstrates several Go
// idioms deliberately different from Python: explicit error returns, typed
// structs, slices, and the standard library's bufio/sort packages.
//
// Usage:
//   go run main.go < somefile.txt      # read from stdin
//   go run main.go words.txt           # read from a file
//
// It prints the top 10 words by frequency.
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"unicode"
)

type wordCount struct {
	word  string
	count int
}

// countWords tokenises the reader into lower-cased words and tallies them.
func countWords(r io.Reader) (map[string]int, error) {
	counts := make(map[string]int)
	scanner := bufio.NewScanner(r)
	scanner.Split(bufio.ScanWords)
	for scanner.Scan() {
		word := strings.ToLower(strings.TrimFunc(scanner.Text(), func(r rune) bool {
			return !unicode.IsLetter(r) && !unicode.IsNumber(r)
		}))
		if word != "" {
			counts[word]++
		}
	}
	// In Go, errors are values you check explicitly — no exceptions.
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return counts, nil
}

// topN returns the n most frequent words, ties broken alphabetically.
func topN(counts map[string]int, n int) []wordCount {
	ranked := make([]wordCount, 0, len(counts))
	for w, c := range counts {
		ranked = append(ranked, wordCount{w, c})
	}
	sort.Slice(ranked, func(i, j int) bool {
		if ranked[i].count != ranked[j].count {
			return ranked[i].count > ranked[j].count
		}
		return ranked[i].word < ranked[j].word
	})
	if n > len(ranked) {
		n = len(ranked)
	}
	return ranked[:n]
}

func main() {
	var reader io.Reader = os.Stdin
	if len(os.Args) > 1 {
		f, err := os.Open(os.Args[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "error opening %s: %v\n", os.Args[1], err)
			os.Exit(1)
		}
		defer f.Close() // defer runs at function exit — Go's cleanup idiom
		reader = f
	}

	counts, err := countWords(reader)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error reading input: %v\n", err)
		os.Exit(1)
	}

	for _, wc := range topN(counts, 10) {
		fmt.Printf("%5d  %s\n", wc.count, wc.word)
	}
}
