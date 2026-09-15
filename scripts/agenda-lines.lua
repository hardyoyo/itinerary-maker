-- Re-render the condensed agenda longtable for LaTeX with no horizontal rules
-- at all — the example's agenda is a ruleless running list. Pandoc always
-- emits \toprule/\bottomrule for tables, so rebuild it as a raw LaTeX
-- longtable, mirroring pandoc's own minipage cell rendering so output is
-- byte-identical except the rules.
-- HTML output is untouched.

local function is_latex()
  return FORMAT:match("latex") ~= nil
end

local function minipage_cell(latex)
  return "\\begin{minipage}[t]{\\linewidth}\\raggedright\n"
    .. latex
    .. "\\strut\n"
    .. "\\end{minipage}"
end

return {
  {
    Table = function(tbl)
      if not is_latex() then
        return nil
      end
      if #tbl.colspecs ~= 2 then
        return nil
      end

      local specs = {}
      for _, colspec in ipairs(tbl.colspecs) do
        local width = 0
        if type(colspec[2]) == "number" then
          width = colspec[2]
        end
        table.insert(
          specs,
          string.format(
            ">{\\raggedright\\arraybackslash}p{(\\linewidth - 2\\tabcolsep) * \\real{%0.4f}}",
            width
          )
        )
      end

      local rows = {}
      for _, body in ipairs(tbl.bodies) do
        for _, row in ipairs(body.body) do
          local cells = {}
          for _, cell in ipairs(row.cells) do
            local content = pandoc.write(pandoc.Pandoc(cell.contents), "latex"):gsub("%s+$", "")
            table.insert(cells, minipage_cell(content))
          end
          table.insert(rows, table.concat(cells, " & "))
        end
      end
      local joined_rows = table.concat(rows, "\\\\\n\\noalign{\\vskip 9pt}") .. "\\\\"

      local latex = string.format([=[
{\def\LTcaptype{none}
\begin{longtable}[]{@{}
  %s
  @{}}
%s
\end{longtable}
}
]=], table.concat(specs, "\n  "), joined_rows)

      return pandoc.RawBlock("latex", latex)
    end,
  },
}