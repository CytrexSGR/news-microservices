#!/bin/bash
# Intelligent Code Navigation - RAG-like dependency tracking
# Usage: ./intelligent_code_nav.sh "function_name" [action]

FUNCTION="$1"
ACTION="${2:-trace}"

echo "🧭 Intelligent Code Navigation: '$FUNCTION'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

case "$ACTION" in
  "trace"|"dependencies")
    echo "📊 Tracing dependencies for: $FUNCTION"
    echo ""

    # Find function definition
    echo "1️⃣ Finding definition..."
    DEFINITION=$(rg -n "def $FUNCTION\(" --type py 2>/dev/null | head -1)

    if [ -n "$DEFINITION" ]; then
      echo "   ✅ Found: $DEFINITION"
      FILE=$(echo "$DEFINITION" | cut -d: -f1)
      LINE=$(echo "$DEFINITION" | cut -d: -f2)
      echo ""

      # Find imports in that file
      echo "2️⃣ Analyzing imports in $FILE..."
      rg "^(from|import)" "$FILE" 2>/dev/null | head -10 | sed 's/^/   📦 /'
      echo ""

      # Find calls to this function
      echo "3️⃣ Finding where $FUNCTION is called..."
      rg "$FUNCTION\(" --type py -l 2>/dev/null | grep -v "$FILE" | head -5 | \
      while read caller; do
        echo "   📞 Called in: $caller"
        rg -C 2 "$FUNCTION\(" "$caller" 2>/dev/null | head -8 | sed 's/^/      /'
        echo ""
      done

      # Find what this function calls
      echo "4️⃣ Analyzing what $FUNCTION calls..."
      sed -n "${LINE},$((LINE+50))p" "$FILE" | \
      rg -o '\b[a-z_]+\(' | sort -u | head -10 | \
      while read callee; do
        callee_name=$(echo "$callee" | sed 's/($//')
        echo "   ➡️  Calls: $callee_name"
      done
    else
      echo "   ❌ Function definition not found"
      echo ""
      echo "   💡 Trying broader search..."
      rg "$FUNCTION" --type py -l 2>/dev/null | head -5 | \
      while read file; do
        echo "   📄 Mentioned in: $file"
      done
    fi
    ;;

  "usage"|"examples")
    echo "📚 Finding usage examples for: $FUNCTION"
    echo ""

    rg -C 3 "$FUNCTION\(" --type py 2>/dev/null | head -50
    ;;

  "imports"|"dependencies")
    echo "📦 Finding import dependencies for: $FUNCTION"
    echo ""

    # Find file containing function
    FILE=$(rg -l "def $FUNCTION\(" --type py 2>/dev/null | head -1)

    if [ -n "$FILE" ]; then
      echo "   📄 File: $FILE"
      echo ""
      echo "   Import tree:"
      rg "^(from|import)" "$FILE" 2>/dev/null | \
      while read import; do
        echo "   ├─ $import"
      done
    fi
    ;;

  *)
    echo "❌ Unknown action: $ACTION"
    echo ""
    echo "Available actions:"
    echo "  - trace       : Trace function dependencies and callers"
    echo "  - usage       : Show usage examples"
    echo "  - imports     : Show import dependencies"
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Tips:"
echo "  - Use 'trace' to understand function flow"
echo "  - Use 'usage' to see real examples"
echo "  - Use 'imports' to check dependencies"
