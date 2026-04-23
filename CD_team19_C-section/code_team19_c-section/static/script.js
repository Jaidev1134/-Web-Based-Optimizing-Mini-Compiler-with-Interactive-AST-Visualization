// Initialize CodeMirror Editor
const editor = CodeMirror.fromTextArea(document.getElementById("editorTextarea"), {
    mode: "javascript",
    theme: "monokai",
    lineNumbers: true,
    tabSize: 4
});
editor.setSize("100%", "500px");

// DOM Elements
const errorBox = document.getElementById("errorBox");
const compileBtn = document.getElementById("compileBtn");
const rawTacBlock = document.getElementById("rawTac");
const optTacBlock = document.getElementById("optTac");
const asmBlock = document.getElementById("asmViewer");
const symbolTableBody = document.getElementById("symbolTableBody");
const chartDiv = document.getElementById("chart");
const cfgSvg = document.getElementById("cfg-svg");
const kregsInput = document.getElementById("kregsInput");

// State
let compileTimeout = null;
let currentTreeData = null;

// Compile Function
async function compile() {
    const code = editor.getValue().trim();
    if (!code) return;

    errorBox.classList.add("d-none");
    errorBox.innerHTML = "";

    try {
        const res = await fetch("/api/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expr: code, k_regs: parseInt(kregsInput.value) || 4 }),
            cache: "no-store"
        });
        const data = await res.json();

        if (data.error && typeof data.error === "string") {
            showError([data.error]);
            clearUI();
            return;
        }

        if (data.errors && data.errors.length > 0) {
            let texts = data.errors.map(e => `Line ${e.line || '?'}: ${e.msg || e}`);
            showError(texts);
        }

        // Render Tree
        if (data.tree) {
            currentTreeData = data.tree;
            drawTree(data.tree);
        } else {
            chartDiv.innerHTML = "<p class='text-secondary text-center p-5'>Syntax Error stopped tree generation.</p>";
        }

        // Render CFG
        if (data.cfg) {
            drawCFG(data.cfg);
        } else {
            cfgSvg.innerHTML = "<text x='10' y='30' fill='#ccc'>Syntax Error stopped CFG generation.</text>";
        }

        // Render TAC
        if (data.raw_tac) { rawTacBlock.textContent = data.raw_tac.join("\n") || "—"; }
        if (data.optimized_tac) { optTacBlock.textContent = data.optimized_tac.join("\n") || "—"; }
        
        // Render ASM
        if (data.assembly) { asmBlock.textContent = data.assembly.join("\n") || "—"; }

        // Render Symbol Table
        if (data.symbol_table) {
            symbolTableBody.innerHTML = "";
            let keys = Object.keys(data.symbol_table);
            if (keys.length === 0) {
                symbolTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No variables assigned.</td></tr>';
            } else {
                for (let k of keys) {
                    let v = data.symbol_table[k];
                    let row = document.createElement("tr");
                    row.innerHTML = `<td><code>${k}</code></td><td>${v.type}</td><td>${v.value !== null ? v.value : '-'}</td>`;
                    symbolTableBody.appendChild(row);
                }
            }
        }

    } catch (e) {
        showError(["Network error or Server issue."]);
        console.error(e);
    }
}

// UI Helpers
function showError(msgs) {
    errorBox.classList.remove("d-none");
    errorBox.innerHTML = msgs.join("<br>");
}

function clearUI() {
    chartDiv.innerHTML = "";
    cfgSvg.innerHTML = "<g/>";
    rawTacBlock.textContent = "—";
    optTacBlock.textContent = "—";
    asmBlock.textContent = "—";
    symbolTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Awaiting Compilation...</td></tr>';
}

function drawCFG(cfgData) {
    if (!window.dagreD3) return;
    const g = new dagreD3.graphlib.Graph().setGraph({
        rankdir: "TB",
        nodesep: 50,
        ranksep: 50,
        marginx: 20,
        marginy: 20
    });

    const isHover = (id) => false; // Could add interactive hovering

    cfgData.nodes.forEach(n => {
        let isPreheader = n.id.startsWith("PH_");
        g.setNode(n.id, {
            label: n.label,
            class: isPreheader ? "cfg-node preheader" : "cfg-node",
            shape: "rect",
            rx: 5,
            ry: 5,
            padding: 10,
            style: isPreheader ? "fill: #198754; stroke: #fff; stroke-width: 2px;" : "fill: #2c3e50; stroke: #adb5bd; stroke-width: 2px;",
            labelStyle: "font-family: monospace; font-size: 14px; fill: #fff; text-align: left;"
        });
    });

    cfgData.edges.forEach(e => {
        g.setEdge(e.from, e.to, {
            curve: d3.curveBasis,
            style: "stroke: #adb5bd; stroke-width: 2px; fill: none;",
            arrowheadStyle: "fill: #adb5bd"
        });
    });

    const svg = d3.select("#cfg-svg");
    const inner = svg.select("g");
    inner.selectAll("*").remove();

    const render = new dagreD3.render();
    
    // Set up zoom support
    const zoom = d3.zoom().on("zoom", function(e) {
        inner.attr("transform", e.transform);
    });
    svg.call(zoom);

    render(inner, g);

    // Center the graph
    const initialScale = 1;
    svg.call(zoom.transform, d3.zoomIdentity.translate(20, 20).scale(initialScale));
}

// Live Compilation Debounce
editor.on("change", () => {
    clearTimeout(compileTimeout);
    compileTimeout = setTimeout(compile, 800);
});
compileBtn.addEventListener("click", compile);

// D3 Tree Rendering
function drawTree(treeData) {
    chartDiv.innerHTML = ""; 

    const root = d3.hierarchy(treeData);
    const treeLayout = d3.tree().nodeSize([60, 60]);
    treeLayout(root);

    let x0 = Infinity, x1 = -x0, y0 = Infinity, y1 = -y0;
    root.each(d => {
        if (d.x > x1) x1 = d.x;
        if (d.x < x0) x0 = d.x;
        if (d.y > y1) y1 = d.y;
        if (d.y < y0) y0 = d.y;
    });

    const minWidth = chartDiv.clientWidth;
    const minHeight = chartDiv.clientHeight + 100;
    
    const svgWidth = Math.max(minWidth, x1 - x0 + 120);
    const svgHeight = Math.max(minHeight, y1 - y0 + 120);

    const svg = d3.select("#chart").append("svg")
        .attr("width", svgWidth)
        .attr("height", svgHeight)
        .style("background", "transparent")
        .append("g")
        .attr("transform", `translate(${Math.max(svgWidth/2, -x0 + 60)}, 40)`);



    // Links
    svg.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y)
        )
        .style("fill", "none")
        .style("stroke", "#555")
        .style("stroke-width", "2px");

    // Nodes
    const node = svg.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);

    // Node circles/boxes
    node.append("circle")
        .attr("r", 15)
        .style("fill", "#0d6efd")
        .style("stroke", "#fff")
        .style("stroke-width", 1);

    // Text label
    node.append("text")
        .attr("dy", ".35em")
        .style("font-family", "monospace")
        .style("font-size", "12px")
        .style("fill", "#fff")
        .attr("text-anchor", "middle")
        .text(d => d.data.name);
}

// Resize observer for tree
new ResizeObserver(() => {
    if (currentTreeData) drawTree(currentTreeData);
}).observe(chartDiv);


// Export Handlers
function downloadTxt(filename, text) {
    if (!text || text === "—") return;
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

document.getElementById("exportTacBtn").addEventListener("click", () => {
    let t1 = rawTacBlock.textContent;
    let t2 = optTacBlock.textContent;
    let final = "=== RAW TAC ===\n" + t1 + "\n\n=== OPTIMIZED TAC ===\n" + t2;
    downloadTxt("TAC_Output.txt", final);
});

document.getElementById("exportAsmBtn").addEventListener("click", () => {
    downloadTxt("MIPS_Assembly.txt", asmBlock.textContent);
});

document.getElementById("exportTreeBtn").addEventListener("click", () => {
    const svgNode = chartDiv.querySelector("svg");
    if(!svgNode) return;
    
    const serializer = new XMLSerializer();
    let svgString = serializer.serializeToString(svgNode);
    if(!svgString.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
        svgString = svgString.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const img = new Image();
    const svgBlob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(svgBlob);
    
    img.onload = function() {
        const canvas = document.createElement("canvas");
        canvas.width = parseInt(svgNode.getAttribute("width"));
        canvas.height = parseInt(svgNode.getAttribute("height"));
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        
        let link = document.createElement("a");
        link.download = "Syntax_Tree_Full.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    };
    img.src = url;
});

document.getElementById("exportCfgBtn").addEventListener("click", () => {
    const svgNode = document.getElementById("cfg-svg");
    if(!svgNode) return;
    
    const serializer = new XMLSerializer();
    let svgString = serializer.serializeToString(svgNode);
    if(!svgString.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
        svgString = svgString.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const img = new Image();
    const svgBlob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(svgBlob);
    
    img.onload = function() {
        const canvas = document.createElement("canvas");
        canvas.width = svgNode.getBoundingClientRect().width;
        canvas.height = Math.max(500, svgNode.getBoundingClientRect().height); // Ensure height exists
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        
        let link = document.createElement("a");
        link.download = "CFG_Diagram.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    };
    img.src = url;
});

// Re-bind compile button without auto-bounce
compileBtn.addEventListener("click", compile);

// Initial compile
compile();
