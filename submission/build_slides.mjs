// Editable native slides. Run through build.sh with the bundled artifact runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, Presentation, PresentationFile } from '@oai/artifact-tool';

const src = process.env.PAP_SUBMISSION_SRC;
const out = process.env.PAP_SUBMISSION_OUT;
const build = process.env.PAP_SUBMISSION_BUILD;
const skill = process.env.PAP_PRESENTATIONS_SKILL;
const raw = JSON.parse(await fs.readFile(path.join(src, 'content.json'), 'utf8'));
const values = { ...raw.facts, repository: raw.repository };
const expand = value => typeof value === 'string'
  ? value.replace(/\{\{(\w+)\}\}/g, (_, key) => {
      if (!(key in values)) throw new Error(`Unknown content variable ${key}`);
      return values[key];
    })
  : Array.isArray(value) ? value.map(expand)
  : value && typeof value === 'object'
    ? Object.fromEntries(Object.entries(value).map(([k, v]) => [k, expand(v)])) : value;
const content = expand(raw);
const { finalizePresentation, resolvePresentationFont } = await import(
  pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href
);
const font = resolvePresentationFont({ fontFamily: 'Arial' });
const C = { bg:'#0B1823', surface:'#102C3D', white:'#F2F7FA', cyan:'#82D4E5', muted:'#B4C9D5', amber:'#E8B362', red:'#EE8883', green:'#91D6BD', edge:'#436374' };
const background = await fs.readFile(path.join(src, 'assets/blueprint.png'));
const screenshot = await fs.readFile(path.join(src, 'assets/pap-console.png'));

function text(slide, value, x, y, w, h, size=24, color=C.white, bold=false, align='left') {
  const shape = slide.shapes.add({geometry:'textbox', position:{left:x,top:y,width:w,height:h}, fill:'none', line:{fill:'none',width:0}});
  shape.text = value;
  shape.text.style = {typeface:font,fontSize:size,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};
  return shape;
}

function box(slide, value, x, y, w, h, color=C.cyan, size=24) {
  const shape = slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:C.surface,line:{fill:color,width:1.6}});
  shape.text = value;
  shape.text.style = {typeface:font,fontSize:size,color:C.white,alignment:'center',verticalAlignment:'middle',autoFit:'none',wrap:'square',insets:{left:12,right:12,top:12,bottom:12}};
  return shape;
}

function arrow(slide, a, b, color=C.cyan, fromSide='right', toSide='left', dashed=false) {
  const shape = slide.shapes.connect(a,b,{kind:'elbow',fromSide,toSide,line:{fill:color,width:2,style:dashed?'dashed':'solid'},tail:{type:'triangle',width:'med',length:'med'}});
  shape.bringToFront();
  return shape;
}

function sourceNotes(data) {
  const refs = data.sources.map(id => {
    const source = content.sources.find(s => s.id === id);
    return `${id}: ${content.repository}/blob/${content.evidence_commit}/${source.path}`;
  });
  return `Planned duration: ${data.seconds} seconds\n\n${data.notes}\n\nEvidence\n${refs.join('\n')}\n\nDesign reference: user-supplied DragonWings_Bounded_Power_Architecture.pdf and DragonWings_Bounded_Power_Forecasting.pptx. Cover illustration: generated conceptual solar and battery blueprint. Console screenshot: actual local Playwright run, September 7, 2026.`;
}

function base(pres, data, index, total, cover=false) {
  const slide = pres.slides.add();
  slide.background.fill = C.bg;
  if (cover) slide.images.add({blob:background,contentType:'image/png',alt:'Conceptual blueprint illustration of solar panels and a portable battery',fit:'cover',position:{left:0,top:0,width:1280,height:720}});
  text(slide,data.checkpoint,64,32,1100,26,17,C.cyan);
  if (!cover) text(slide,data.title,64,76,1152,94,43,C.white,true);
  text(slide,`${index} / ${total}`,1150,688,66,20,14,C.muted,false,'right');
  slide.speakerNotes.textFrame.setText(sourceNotes(data));
  return slide;
}

function meaning(slide,data) {
  text(slide,'What it does',64,563,500,25,18,C.cyan,true);
  text(slide,data.what,64,595,536,65,24);
  text(slide,'Why it matters',680,563,500,25,18,C.amber,true);
  text(slide,data.why,680,595,536,65,24);
  if(data.caveat) text(slide,data.caveat,64,673,1070,23,16,C.muted);
}

function nativeTable(slide, headers, rows, x,y,width,height,widths) {
  const table=slide.tables.add({rows:rows.length+1,columns:headers.length,left:x,top:y,width,height,columnWidths:widths,values:[headers,...rows]});
  table.borders.assign({fill:C.edge,width:1,style:'solid'});
  table.cells.block({row:0,column:0,rowCount:rows.length+1,columnCount:headers.length}).assign({
    fill:C.surface,textStyle:{typeface:font,fontSize:22,color:C.white},margins:{left:16,right:16,top:10,bottom:10},anchor:'center'
  });
  for(let r=0;r<=rows.length;r++) {
    table.rows[r].height=height/(rows.length+1);
    for(let c=0;c<headers.length;c++) {
      const cell=table.getCell(r,c);
      cell.text.style={typeface:font,fontSize:22,color:r===0?C.cyan:C.white,bold:r===0,verticalAlignment:'middle'};
      cell.fill=r===0?'#183E50':C.surface;
    }
  }
  return table;
}

function renderSlide(pres,d,i,total) {
  const s=base(pres,d,i,total,['cover','pitch_problem'].includes(d.kind));
  switch(d.kind) {
    case 'cover':
      text(s,d.title,64,175,750,245,64,C.white,true);
      text(s,d.subtitle,64,455,700,100,30,C.cyan);
      text(s,d.plain,64,570,700,60,24,C.muted);
      text(s,`${content.author}\n${content.date}`,64,642,600,58,19,C.white);
      break;
    case 'problem': {
      text(s,d.question,64,178,1120,65,33,C.white);
      const inp=d.inputs.map((label,j)=>box(s,label,64,275+j*73,255,57,C.cyan,24));
      const result=box(s,d.output,500,310,280,122,C.amber,28);
      const human=box(s,d.human,960,310,255,122,C.cyan,26);
      inp.forEach(x=>arrow(s,x,result));
      arrow(s,result,human,C.amber);
      meaning(s,d); break;
    }
    case 'architecture': {
      const steps=d.nodes.map(([label,detail],j)=>box(s,`${label}\n${detail}`,64+j*304,211,235,105,j===3?C.red:C.cyan,23));
      steps.slice(1).forEach((b,j)=>arrow(s,steps[j],b));
      const model=box(s,d.model,625,387,328,92,C.amber,24);
      arrow(s,steps[2],model,C.amber,'bottom','top',true);
      arrow(s,model,steps[3],C.amber,'right','bottom',true);
      text(s,d.branch,64,402,480,70,25,C.amber);
      text(s,d.storage,64,507,1120,32,21,C.muted);
      meaning(s,d); break;
    }
    case 'memory': {
      const steps=d.nodes.map(([label,detail],j)=>box(s,`${label}\n${detail}`,64+j*304,232,235,120,C.cyan,24));
      steps.slice(1).forEach((b,j)=>arrow(s,steps[j],b));
      const dest=box(s,d.destination,720,430,495,70,C.amber,26);
      arrow(s,steps[3],dest,C.amber,'bottom','top');
      text(s,'Outcomes become evidence for a later run',64,437,560,70,26,C.muted);
      meaning(s,d); break;
    }
    case 'search': {
      const a=box(s,d.routine,64,195,300,75,C.cyan,26);
      const b=box(s,d.routine_end,916,195,300,75,C.red,25);
      arrow(s,a,b);
      text(s,'Direct path without model generation',400,284,480,56,24,C.muted);
      const amb=box(s,d.ambiguous,64,350,210,96,C.amber,24);
      const nodes=d.nodes.map((value,j)=>box(s,value,324+j*235,350,185,96,C.amber,23));
      [amb,...nodes].slice(1).forEach((n,j)=>arrow(s,[amb,...nodes][j],n,C.amber));
      arrow(s,nodes[3],b,C.amber,'top','bottom');
      text(s,d.bounds,64,489,1152,54,24,C.muted);
      meaning(s,d); break;
    }
    case 'comparison': {
      const roles=[d.roles[2],d.roles[0],d.roles[1]];
      const nodes=roles.map((value,j)=>box(s,value,64+j*400,190,j===2?352:320,78,C.amber,25));
      arrow(s,nodes[0],nodes[1],C.amber,'right','left',true);
      arrow(s,nodes[1],nodes[2],C.amber);
      nativeTable(s,d.headers,d.rows,64,315,1152,160,[470,190,220,272]);
      text(s,d.finding,64,498,1120,47,31,C.cyan,true);
      meaning(s,d); break;
    }
    case 'safety': {
      const checks=d.checks.map((value,j)=>box(s,value,64+j*304,204,235,77,C.red,24));
      checks.slice(1).forEach((b,j)=>arrow(s,checks[j],b,C.red));
      text(s,d.floor,64,336,450,105,77,C.white,true);
      text(s,d.floor_label,64,446,475,46,25,C.muted);
      box(s,d.outcomes[0],660,348,555,66,C.green,25);
      box(s,d.outcomes[1],660,443,555,66,C.red,25);
      meaning(s,d); break;
    }
    case 'console':
      s.images.add({blob:screenshot,contentType:'image/png',alt:'Actual local PAP console showing a withheld decision and its inspector tabs',fit:'contain',position:{left:64,top:177,width:812,height:355}});
      d.tabs.forEach(([label,detail],j)=>{
        text(s,label,911,176+j*61,305,28,24,C.cyan,true);
        text(s,detail,911,205+j*61,305,33,19,C.muted);
      });
      meaning(s,d); break;
    case 'evaluation':
      d.counts.forEach(([number,label],j)=>{
        text(s,number,64+j*275,192,260,110,80,C.cyan,true);
        text(s,label,64+j*275,310,245,80,27,C.white);
      });
      text(s,d.point_title,662,198,550,68,30,C.white,true);
      nativeTable(s,['Point-power metric','Error'],d.point_rows,662,294,554,184,[346,208]);
      text(s,'Reproducible local gate',64,451,545,50,27,C.muted);
      meaning(s,d); break;
    case 'closing':
      text(s,content.repository,64,175,1152,60,34,C.cyan);
      d.files.forEach(([label,detail],j)=>{
        text(s,label,64,255+j*55,600,25,23,C.white,true);
        text(s,detail,64,282+j*55,600,25,20,C.muted);
      });
      text(s,'Next improvements',780,255,436,40,28,C.amber,true);
      d.next.forEach((value,j)=>text(s,value,780,316+j*72,436,66,25,C.white));
      text(s,d.commands.join('\n'),64,489,666,68,18,C.cyan);
      meaning(s,d); break;
    case 'pitch_problem':
      text(s,d.title,64,176,800,250,64,C.white,true);
      text(s,d.subtitle,64,463,735,108,34,C.cyan);
      text(s,content.author,64,640,700,38,25,C.white);
      break;
    case 'pitch_flow': {
      const steps=d.nodes.map((value,j)=>box(s,value,64+j*304,242,235,136,j===2?C.amber:j===3?C.red:C.cyan,31));
      steps.slice(1).forEach((b,j)=>arrow(s,steps[j],b,j===2?C.red:C.cyan));
      text(s,d.plain,64,462,1152,100,37,C.white,true);
      text(s,d.boundary,64,613,1110,65,27,C.muted);
      break;
    }
    case 'pitch_proof':
      text(s,d.proof,64,230,1145,125,43,C.cyan,true);
      text(s,d.takeaway,64,425,1145,80,35,C.white,true);
      text(s,d.limit,64,540,1145,50,28,C.amber);
      text(s,content.repository,64,633,1130,50,29,C.cyan);
      break;
    default: throw new Error(`Unknown slide kind ${d.kind}`);
  }
  return s;
}

async function deck(slides,name,tableSlides) {
  const pres=Presentation.create({slideSize:{width:1280,height:720}});
  slides.forEach((data,index)=>renderSlide(pres,data,index+1,slides.length));
  const work=path.join(build,name);
  await fs.mkdir(work,{recursive:true});
  const candidatePath=path.join(work,'candidate.pptx');
  await (await PresentationFile.exportPptx(pres)).save(candidatePath);
  const finalPath=path.join(out,name+'.pptx');
  await finalizePresentation({
    workspaceDir:process.env.PAP_REPO_ROOT,candidatePath,finalPath,
    pythonExecutable:process.env.RUNTIME_PYTHON,
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],
    explicitTotalSlideCount:slides.length,requiredNativeTableOwnerSlides:tableSlides,
    fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
    receiptPath:path.join(work,'validation.json')
  });
  const finalDeck=await PresentationFile.importPptx(await FileBlob.load(finalPath));
  for(let index=0;index<finalDeck.slides.items.length;index++) {
    const preview=await finalDeck.export({slide:finalDeck.slides.items[index],format:'png',scale:2});
    await fs.writeFile(path.join(work,`slide-${index+1}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  console.log(`Created ${finalPath}`);
}

await deck(content.slides,'DragonWings_Final_Presentation',[6,9]);
await deck(content.pitch_slides,'DragonWings_90_Second_Pitch',[]);
