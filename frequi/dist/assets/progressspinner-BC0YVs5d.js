import{A as e,L as t,N as n,Pt as r,Q as i,T as a,X as o,_t as s,at as c,c as l,d as u,g as d,h as f,it as p,l as m,lt as h,r as g,u as _}from"./runtime-core.esm-bundler-C7KLiCKn.js";import{B as v,V as y,_t as b,ft as x,on as S,sn as C,tn as w,ur as T}from"./index-BYaZKrEj.js";import{t as E}from"./plus-box-outline-CSTmQeXt.js";import{t as D}from"./check-BiHwlxIO.js";var O={name:`InputGroup`,extends:{name:`BaseInputGroup`,extends:S,style:C.extend({name:`inputgroup`,style:`
    .p-inputgroup,
    .p-inputgroup .p-iconfield,
    .p-inputgroup .p-floatlabel,
    .p-inputgroup .p-iftalabel {
        display: flex;
        align-items: stretch;
        width: 100%;
    }

    .p-inputgroup .p-floatlabel .p-inputwrapper,
    .p-inputgroup .p-iftalabel .p-inputwrapper {
        display: inline-flex;
    }

    .p-inputgroup .p-inputtext,
    .p-inputgroup .p-inputwrapper {
        flex: 1 1 auto;
        width: 1%;
    }

    .p-inputgroupaddon {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: dt('inputgroup.addon.padding');
        background: dt('inputgroup.addon.background');
        color: dt('inputgroup.addon.color');
        border-block-start: 1px solid dt('inputgroup.addon.border.color');
        border-block-end: 1px solid dt('inputgroup.addon.border.color');
        min-width: dt('inputgroup.addon.min.width');
    }

    .p-inputgroupaddon:first-child,
    .p-inputgroupaddon + .p-inputgroupaddon {
        border-inline-start: 1px solid dt('inputgroup.addon.border.color');
    }

    .p-inputgroupaddon:last-child {
        border-inline-end: 1px solid dt('inputgroup.addon.border.color');
    }

    .p-inputgroupaddon:has(.p-button) {
        padding: 0;
        overflow: hidden;
    }

    .p-inputgroupaddon .p-button {
        border-radius: 0;
    }

    .p-inputgroup > .p-component,
    .p-inputgroup > .p-inputwrapper > .p-component,
    .p-inputgroup > .p-iconfield > .p-component,
    .p-inputgroup > .p-floatlabel > .p-component,
    .p-inputgroup > .p-floatlabel > .p-inputwrapper > .p-component,
    .p-inputgroup > .p-iftalabel > .p-component,
    .p-inputgroup > .p-iftalabel > .p-inputwrapper > .p-component {
        border-radius: 0;
        margin: 0;
    }

    .p-inputgroupaddon:first-child,
    .p-inputgroup > .p-component:first-child,
    .p-inputgroup > .p-inputwrapper:first-child > .p-component,
    .p-inputgroup > .p-iconfield:first-child > .p-component,
    .p-inputgroup > .p-floatlabel:first-child > .p-component,
    .p-inputgroup > .p-floatlabel:first-child > .p-inputwrapper > .p-component,
    .p-inputgroup > .p-iftalabel:first-child > .p-component,
    .p-inputgroup > .p-iftalabel:first-child > .p-inputwrapper > .p-component {
        border-start-start-radius: dt('inputgroup.addon.border.radius');
        border-end-start-radius: dt('inputgroup.addon.border.radius');
    }

    .p-inputgroupaddon:last-child,
    .p-inputgroup > .p-component:last-child,
    .p-inputgroup > .p-inputwrapper:last-child > .p-component,
    .p-inputgroup > .p-iconfield:last-child > .p-component,
    .p-inputgroup > .p-floatlabel:last-child > .p-component,
    .p-inputgroup > .p-floatlabel:last-child > .p-inputwrapper > .p-component,
    .p-inputgroup > .p-iftalabel:last-child > .p-component,
    .p-inputgroup > .p-iftalabel:last-child > .p-inputwrapper > .p-component {
        border-start-end-radius: dt('inputgroup.addon.border.radius');
        border-end-end-radius: dt('inputgroup.addon.border.radius');
    }

    .p-inputgroup .p-component:focus,
    .p-inputgroup .p-component.p-focus,
    .p-inputgroup .p-inputwrapper-focus,
    .p-inputgroup .p-component:focus ~ label,
    .p-inputgroup .p-component.p-focus ~ label,
    .p-inputgroup .p-inputwrapper-focus ~ label,
    .p-inputgroup .p-floatlabel .p-inputwrapper ~ label,
    .p-inputgroup .p-iftalabel .p-inputwrapper ~ label {
        z-index: 1;
    }

    .p-inputgroup > .p-button:not(.p-button-icon-only) {
        width: auto;
    }

    .p-inputgroup .p-iconfield + .p-iconfield .p-inputtext {
        border-inline-start: 0;
    }
`,classes:{root:`p-inputgroup`}}),provide:function(){return{$pcInputGroup:this,$parentInstance:this}}},inheritAttrs:!1};function k(e,r,i,o,s,c){return n(),u(`div`,a({class:e.cx(`root`)},e.ptmi(`root`)),[t(e.$slots,`default`)],16)}O.render=k;var A={name:`InputGroupAddon`,extends:{name:`BaseInputGroupAddon`,extends:S,style:C.extend({name:`inputgroupaddon`,classes:{root:`p-inputgroupaddon`}}),provide:function(){return{$pcInputGroupAddon:this,$parentInstance:this}}},inheritAttrs:!1};function j(e,r,i,o,s,c){return n(),u(`div`,a({class:e.cx(`root`)},e.ptmi(`root`)),[t(e.$slots,`default`)],16)}A.render=j;var M={viewBox:`0 0 24 24`,width:`1.2em`,height:`1.2em`};function N(e,t){return n(),u(`svg`,M,[...t[0]||=[l(`path`,{fill:`currentColor`,d:`M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12z`},null,-1)]])}var P=c({name:`mdi-content-copy`,render:N}),F={class:`grow`},I=function(e){return e[e.None=0]=`None`,e[e.Editing=1]=`Editing`,e[e.Adding=2]=`Adding`,e[e.Duplicating=3]=`Duplicating`,e}(I||{}),L=d({__name:`EditValue`,props:{modelValue:{},allowEdit:{type:Boolean,default:!1},allowAdd:{type:Boolean,default:!1},allowDuplicate:{type:Boolean,default:!1},editableName:{},alignVertical:{type:Boolean,default:!1}},emits:[`delete`,`new`,`duplicate`,`rename`],setup(a,{emit:c}){let d=a,S=c,C=h(``),O=h(I.None);e(()=>{C.value=d.modelValue});function k(){O.value=I.None,C.value=d.modelValue}function A(){C.value+=` (copy)`,O.value=I.Duplicating}function j(){C.value=``,O.value=I.Adding}o(()=>d.modelValue,()=>{C.value=d.modelValue});function M(){O.value===I.Adding?S(`new`,C.value):O.value===I.Duplicating?S(`duplicate`,d.modelValue,C.value):S(`rename`,d.modelValue,C.value),O.value=I.None}return(e,o)=>{let c=x,d=v,h=w,S=P,N=y,L=E,R=D,z=b;return n(),u(`form`,{class:`flex flex-row`,onSubmit:T(M,[`prevent`])},[l(`div`,F,[s(O)===I.None?t(e.$slots,`default`,{key:0}):(n(),m(c,{key:1,modelValue:s(C),"onUpdate:modelValue":o[0]||=e=>p(C)?C.value=e:null,size:`small`,fluid:``},null,8,[`modelValue`]))]),l(`div`,{class:r([`mt-auto flex gap-1 ms-1`,a.alignVertical?`flex-col`:`flex-row`])},[a.allowEdit&&s(O)===I.None?(n(),u(g,{key:0},[f(h,{size:`small`,severity:`secondary`,title:`Edit this ${a.editableName}.`,onClick:o[1]||=e=>O.value=I.Editing},{icon:i(()=>[f(d)]),_:1},8,[`title`]),a.allowDuplicate?(n(),m(h,{key:0,size:`small`,severity:`secondary`,title:`Duplicate ${a.editableName}.`,onClick:A},{icon:i(()=>[f(S)]),_:1},8,[`title`])):_(``,!0),f(h,{size:`small`,severity:`secondary`,title:`Delete this ${a.editableName}.`,onClick:o[2]||=t=>e.$emit(`delete`,a.modelValue)},{icon:i(()=>[f(N)]),_:1},8,[`title`])],64)):_(``,!0),a.allowAdd&&s(O)===I.None?(n(),m(h,{key:1,size:`small`,title:`Add new ${a.editableName}.`,severity:`primary`,onClick:j},{icon:i(()=>[f(L)]),_:1},8,[`title`])):_(``,!0),s(O)===I.None?_(``,!0):(n(),u(g,{key:2},[f(h,{size:`small`,title:`Add new ${a.editableName}`,severity:`primary`,onClick:M},{icon:i(()=>[f(R)]),_:1},8,[`title`]),f(h,{size:`small`,title:`Abort`,severity:`secondary`,onClick:k},{icon:i(()=>[f(z)]),_:1})],64))],2)],32)}}}),R=C.extend({name:`progressspinner`,style:`
    .p-progressspinner {
        position: relative;
        margin: 0 auto;
        width: 100px;
        height: 100px;
        display: inline-block;
    }

    .p-progressspinner::before {
        content: '';
        display: block;
        padding-top: 100%;
    }

    .p-progressspinner-spin {
        height: 100%;
        transform-origin: center center;
        width: 100%;
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        margin: auto;
        animation: p-progressspinner-rotate 2s linear infinite;
    }

    .p-progressspinner-circle {
        stroke-dasharray: 89, 200;
        stroke-dashoffset: 0;
        stroke: dt('progressspinner.colorOne');
        animation:
            p-progressspinner-dash 1.5s ease-in-out infinite,
            p-progressspinner-color 6s ease-in-out infinite;
        stroke-linecap: round;
    }

    @keyframes p-progressspinner-rotate {
        100% {
            transform: rotate(360deg);
        }
    }
    @keyframes p-progressspinner-dash {
        0% {
            stroke-dasharray: 1, 200;
            stroke-dashoffset: 0;
        }
        50% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -35px;
        }
        100% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -124px;
        }
    }
    @keyframes p-progressspinner-color {
        100%,
        0% {
            stroke: dt('progressspinner.color.one');
        }
        40% {
            stroke: dt('progressspinner.color.two');
        }
        66% {
            stroke: dt('progressspinner.color.three');
        }
        80%,
        90% {
            stroke: dt('progressspinner.color.four');
        }
    }
`,classes:{root:`p-progressspinner`,spin:`p-progressspinner-spin`,circle:`p-progressspinner-circle`}}),z={name:`ProgressSpinner`,extends:{name:`BaseProgressSpinner`,extends:S,props:{strokeWidth:{type:String,default:`2`},fill:{type:String,default:`none`},animationDuration:{type:String,default:`2s`}},style:R,provide:function(){return{$pcProgressSpinner:this,$parentInstance:this}}},inheritAttrs:!1,computed:{svgStyle:function(){return{"animation-duration":this.animationDuration}}}},B=[`fill`,`stroke-width`];function V(e,t,r,i,o,s){return n(),u(`div`,a({class:e.cx(`root`),role:`progressbar`},e.ptmi(`root`)),[(n(),u(`svg`,a({class:e.cx(`spin`),viewBox:`25 25 50 50`,style:s.svgStyle},e.ptm(`spin`)),[l(`circle`,a({class:e.cx(`circle`),cx:`50`,cy:`50`,r:`20`,fill:e.fill,"stroke-width":e.strokeWidth,strokeMiterlimit:`10`},e.ptm(`circle`)),null,16,B)],16))],16)}z.render=V;export{O as a,A as i,L as n,P as r,z as t};
//# sourceMappingURL=progressspinner-BC0YVs5d.js.map