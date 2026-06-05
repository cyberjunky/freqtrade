import{$ as e,I as t,L as n,N as r,Q as i,Rt as a,T as o,_t as s,at as c,c as l,d as u,g as d,h as f,it as p,l as m,lt as h,m as g,r as _,s as v,u as y}from"./runtime-core.esm-bundler-C7KLiCKn.js";import{n as b,r as ee,t as x}from"./pairlistConfig-BuDzImJY.js";import{t as S}from"./TimeRangeSelect-DnMfcFPE.js";import{Qt as C,Tt as w,V as T,Xt as E,ar as D,cr as O,ht as te,it as k,kt as A,on as j,ot as M,sn as N,tn as P,tr as F,vt as ne,wt as I}from"./index-BYaZKrEj.js";import{t as L}from"./inputnumber-DifGz0vL.js";import{t as R}from"./DraggableContainer-CAOKMujh.js";import{t as z}from"./check-BiHwlxIO.js";import{t as B}from"./multiselect-C-2uE8UI.js";import{t as V}from"./ExchangeSelect-DTErdS0u.js";var H=N.extend({name:`progressbar`,style:`
    .p-progressbar {
        display: block;
        position: relative;
        overflow: hidden;
        height: dt('progressbar.height');
        background: dt('progressbar.background');
        border-radius: dt('progressbar.border.radius');
    }

    .p-progressbar-value {
        margin: 0;
        background: dt('progressbar.value.background');
    }

    .p-progressbar-label {
        color: dt('progressbar.label.color');
        font-size: dt('progressbar.label.font.size');
        font-weight: dt('progressbar.label.font.weight');
    }

    .p-progressbar-determinate .p-progressbar-value {
        height: 100%;
        width: 0%;
        position: absolute;
        display: none;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        transition: width 1s ease-in-out;
    }

    .p-progressbar-determinate .p-progressbar-label {
        display: inline-flex;
    }

    .p-progressbar-indeterminate .p-progressbar-value::before {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim 2.1s cubic-bezier(0.65, 0.815, 0.735, 0.395) infinite;
    }

    .p-progressbar-indeterminate .p-progressbar-value::after {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim-short 2.1s cubic-bezier(0.165, 0.84, 0.44, 1) infinite;
        animation-delay: 1.15s;
    }

    @keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }

    @keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
`,classes:{root:function(e){var t=e.instance;return[`p-progressbar p-component`,{"p-progressbar-determinate":t.determinate,"p-progressbar-indeterminate":t.indeterminate}]},value:`p-progressbar-value`,label:`p-progressbar-label`}}),U={name:`ProgressBar`,extends:{name:`BaseProgressBar`,extends:j,props:{value:{type:Number,default:null},mode:{type:String,default:`determinate`},showValue:{type:Boolean,default:!0}},style:H,provide:function(){return{$pcProgressBar:this,$parentInstance:this}}},inheritAttrs:!1,computed:{progressStyle:function(){return{width:this.value+`%`,display:`flex`}},indeterminate:function(){return this.mode===`indeterminate`},determinate:function(){return this.mode===`determinate`},dataP:function(){return F({determinate:this.determinate,indeterminate:this.indeterminate})}}},W=[`aria-valuenow`,`data-p`],G=[`data-p`],K=[`data-p`],q=[`data-p`];function J(e,t,i,s,c,l){return r(),u(`div`,o({role:`progressbar`,class:e.cx(`root`),"aria-valuemin":`0`,"aria-valuenow":e.value,"aria-valuemax":`100`,"data-p":l.dataP},e.ptmi(`root`)),[l.determinate?(r(),u(`div`,o({key:0,class:e.cx(`value`),style:l.progressStyle,"data-p":l.dataP},e.ptm(`value`)),[e.value!=null&&e.value!==0&&e.showValue?(r(),u(`div`,o({key:0,class:e.cx(`label`),"data-p":l.dataP},e.ptm(`label`)),[n(e.$slots,`default`,{},function(){return[g(a(e.value+`%`),1)]})],16,K)):y(``,!0)],16,G)):l.indeterminate?(r(),u(`div`,o({key:1,class:e.cx(`value`),"data-p":l.dataP},e.ptm(`value`)),null,16,q)):y(``,!0)],16,W)}U.render=J;var Y={viewBox:`0 0 24 24`,width:`1.2em`,height:`1.2em`};function X(e,t){return r(),u(`svg`,Y,[...t[0]||=[l(`path`,{fill:`currentColor`,d:`M8 17v-2h8v2zm8-7l-4 4l-4-4h2.5V7h3v3zM5 3h14a2 2 0 0 1 2 2v14c0 1.11-.89 2-2 2H5a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2m0 2v14h14V5z`},null,-1)]])}var Z=c({name:`mdi-download-box-outline`,render:X}),Q={class:`flex flex-row items-end gap-1`},re={class:`ms-2 w-full grow space-y-1`},ie=[`title`],ae={key:1},oe={class:`flex justify-between`},se={key:1},ce={key:2,class:`w-25`},le={key:3,class:`flex flex-col md:flex-row w-full grow gap-2`},ue=d({__name:`BackgroundJobTracking`,setup(e){let{runningJobs:n,clearJobs:o}=A();return(e,c)=>{let d=Z,p=z,h=U,v=T,b=P;return r(),u(`div`,Q,[l(`ul`,re,[(r(!0),u(_,null,t(s(n),(e,n)=>(r(),u(`li`,{key:n,class:`border p-1 pb-2 rounded-sm dark:border-surface-700 border-surface-300 flex gap-2 items-center`,title:n},[e.taskStatus?.job_category===`download_data`?(r(),m(d,{key:0})):(r(),u(`span`,ae,a(e.taskStatus?.job_category),1)),l(`div`,oe,[e.taskStatus?.status===`success`?(r(),m(p,{key:0,class:`text-success`,title:``})):(r(),u(`span`,se,a(e.taskStatus?.status),1)),e.taskStatus?.progress?(r(),u(`span`,ce,a(e.taskStatus?.progress),1)):y(``,!0)]),e.taskStatus?.progress?(r(),m(h,{key:2,class:`w-full grow`,value:e.taskStatus?.progress/100*100,"show-progress":``,max:100,striped:``},null,8,[`value`])):y(``,!0),e.taskStatus?.progress_tasks?(r(),u(`div`,le,[(r(!0),u(_,null,t(Object.entries(e.taskStatus?.progress_tasks),([t,n])=>(r(),u(`div`,{key:t,class:`w-full`},[g(a(n.description)+` `,1),f(h,{class:`w-full grow`,value:Math.round(n.progress/n.total*100*100)/100,"show-progress":``,pt:{value:{class:e.taskStatus.status===`success`?`bg-emerald-500`:`bg-amber-500`}},striped:``},null,8,[`value`,`pt`])]))),128))])):y(``,!0)],8,ie))),128))]),Object.keys(s(n)).length>0?(r(),m(b,{key:0,severity:`secondary`,class:`ms-auto`,onClick:s(o)},{icon:i(()=>[f(v)]),_:1},8,[`onClick`])):y(``,!0)])}}}),de=h([{description:`All USDT Pairs`,pairs:[`.*/USDT`]},{description:`All USDT Futures Pairs`,pairs:[`.*/USDT:USDT`]}]);function fe(){return{pairTemplates:v(()=>de.value.map((e,t)=>({...e,idx:t})))}}var pe={class:`px-1 mx-auto w-full max-w-4xl lg:max-w-7xl`},me={class:`flex mb-3 gap-3 flex-col`},he={class:`flex flex-col gap-3`},ge={class:`flex flex-col lg:flex-row gap-3`},_e={class:`flex-fill`},ve={class:`flex flex-col gap-2`},ye={class:`flex gap-2`},be={class:`flex flex-col gap-1`},xe={class:`flex flex-col gap-1`},Se={class:`flex-fill px-3`},Ce={class:`flex flex-col gap-2`},we={class:`px-3 border dark:border-surface-700 border-surface-300 p-2 rounded-sm`},$={class:`flex flex-col gap-2`},Te={class:`flex justify-between items-center`},Ee={key:0},De={key:1,class:`flex items-center gap-2`},Oe={class:`mb-2 border dark:border-surface-700 border-surface-300 rounded-sm p-2 text-start`},ke={class:`mb-2 border dark:border-surface-700 border-surface-300 rounded-md p-2 text-start`},Ae={class:`grid grid-cols md:grid-cols-2 items-center gap-2`},je={class:`mb-2 border dark:border-surface-700 border-surface-300 rounded-md p-2 text-start`},Me={class:`px-3`},Ne=d({__name:`DownloadDataMain`,setup(n){let o=w(),c=x(),d=h([`BTC/USDT`,`ETH/USDT`,``]),v=h([`5m`,`1h`]),T=h({useCustomTimerange:!1,timerange:``,days:30}),{pairTemplates:A}=fe(),j=h({customExchange:!1,selectedExchange:{exchange:`binance`,trade_mode:{margin_mode:E.NONE,trading_mode:C.SPOT}}}),N=h({erase:!1,prepend_data:!1,downloadTrades:!1,candleTypes:[]}),F=h(!1),I=[{text:`Spot`,value:`spot`},{text:`Futures`,value:`futures`},{text:`Funding Rate`,value:`funding_rate`},{text:`Mark`,value:`mark`},{text:`Index`,value:`index`},{text:`Premium Index`,value:`premiumIndex`}];function z(e){d.value.push(...e)}function H(e){d.value=[...e]}async function U(){let e={pairs:d.value.filter(e=>e!==``),timeframes:v.value.filter(e=>e!==``)};T.value.useCustomTimerange&&T.value.timerange?e.timerange=T.value.timerange:e.days=T.value.days,F.value&&(e.erase=N.value.erase,e.download_trades=N.value.downloadTrades,j.value.customExchange&&(e.exchange=j.value.selectedExchange.exchange,e.trading_mode=j.value.selectedExchange.trade_mode.trading_mode,e.margin_mode=j.value.selectedExchange.trade_mode.margin_mode),o.activeBot.botFeatures.downloadDataCandleTypes&&N.value.candleTypes.length>0&&(e.candle_types=N.value.candleTypes),o.activeBot.botFeatures.downloadDataPrepend&&N.value.prepend_data&&(e.prepend_data=!0)),await o.activeBot.startDataDownload(e)}return(n,h)=>{let x=ue,C=b,w=P,E=ne,W=M,G=S,K=L,q=k,J=ee,Y=te,X=B,Z=V,Q=R;return r(),u(`div`,pe,[f(x,{class:`mb-4`}),f(Q,{header:`Downloading Data`,class:`mx-1 p-4`},{default:i(()=>[l(`div`,me,[l(`div`,he,[l(`div`,ge,[l(`div`,_e,[l(`div`,ve,[h[14]||=l(`div`,{class:`flex justify-between`},[l(`h4`,{class:`text-start font-bold text-lg`},`Select Pairs`),l(`h5`,{class:`text-start font-bold text-lg`},`Pairs from template`)],-1),l(`div`,ye,[f(C,{modelValue:s(d),"onUpdate:modelValue":h[0]||=e=>p(d)?d.value=e:null,placeholder:`Pair`,size:`small`,class:`grow`},null,8,[`modelValue`]),l(`div`,be,[l(`div`,xe,[(r(!0),u(_,null,t(s(A),e=>(r(),m(w,{key:e.idx,severity:`secondary`,title:e.pairs.reduce((e,t)=>`${e}${t}\n`,``),onClick:t=>z(e.pairs)},{default:i(()=>[g(a(e.description),1)]),_:2},1032,[`title`,`onClick`]))),128))]),f(E),f(w,{disabled:s(c).whitelist.length===0,title:`Add all pairs from Pairlist Config - requires the pairlist config to have ran first.`,severity:`secondary`,onClick:h[1]||=e=>H(s(c).whitelist)},{default:i(()=>[...h[13]||=[g(` Use Pairs from Pairlist Config `,-1)]]),_:1},8,[`disabled`])])])])]),l(`div`,Se,[l(`div`,Ce,[h[15]||=l(`h4`,{class:`text-start font-bold text-lg`},`Select timeframes`,-1),f(C,{modelValue:s(v),"onUpdate:modelValue":h[2]||=e=>p(v)?v.value=e:null,placeholder:`Timeframe`},null,8,[`modelValue`])])])]),l(`div`,we,[l(`div`,$,[l(`div`,Te,[h[17]||=l(`h4`,{class:`text-start mb-0 font-bold text-lg`},`Time Selection`,-1),f(W,{modelValue:s(T).useCustomTimerange,"onUpdate:modelValue":h[3]||=e=>s(T).useCustomTimerange=e,class:`mb-0`,switch:``},{default:i(()=>[...h[16]||=[g(` Use custom timerange `,-1)]]),_:1},8,[`modelValue`])]),s(T).useCustomTimerange?(r(),u(`div`,Ee,[f(G,{modelValue:s(T).timerange,"onUpdate:modelValue":h[4]||=e=>s(T).timerange=e},null,8,[`modelValue`])])):(r(),u(`div`,De,[h[18]||=l(`label`,null,`Days to download:`,-1),f(K,{modelValue:s(T).days,"onUpdate:modelValue":h[5]||=e=>s(T).days=e,type:`number`,"aria-label":`Days to download`,min:1,step:1,size:`small`},null,8,[`modelValue`])]))])]),l(`div`,Oe,[f(w,{class:`mb-2`,severity:`secondary`,onClick:h[6]||=e=>F.value=!s(F)},{default:i(()=>[h[19]||=g(` Advanced Options `,-1),s(F)?(r(),m(J,{key:1})):(r(),m(q,{key:0}))]),_:1}),f(D,null,{default:i(()=>[e(l(`div`,null,[f(Y,{severity:`info`,class:`mb-2 py-2`},{default:i(()=>[...h[20]||=[g(` Advanced options (Erase data, Download trades, and Custom Exchange settings) will only be applied when this section is expanded. `,-1)]]),_:1}),l(`div`,ke,[f(W,{modelValue:s(N).erase,"onUpdate:modelValue":h[7]||=e=>s(N).erase=e,class:`mb-2`},{default:i(()=>[...h[21]||=[g(`Erase existing data`,-1)]]),_:1},8,[`modelValue`]),s(o).activeBot.botFeatures.downloadDataPrepend?(r(),m(W,{key:0,modelValue:s(N).prepend_data,"onUpdate:modelValue":h[8]||=e=>s(N).prepend_data=e,class:`mb-2`},{default:i(()=>[...h[22]||=[g(`Prepend data when downloading`,-1)]]),_:1},8,[`modelValue`])):y(``,!0),f(W,{modelValue:s(N).downloadTrades,"onUpdate:modelValue":h[9]||=e=>s(N).downloadTrades=e,class:`mb-2`},{default:i(()=>[...h[23]||=[g(` Download Trades instead of OHLCV data `,-1)]]),_:1},8,[`modelValue`]),l(`div`,Ae,[s(o).activeBot.botFeatures.downloadDataCandleTypes?(r(),m(X,{key:0,modelValue:s(N).candleTypes,"onUpdate:modelValue":h[10]||=e=>s(N).candleTypes=e,options:I,"option-label":`text`,"option-value":`value`,placeholder:`Select Candle Types`},null,8,[`modelValue`])):y(``,!0),h[24]||=l(`small`,null,`When no candle-type is selected, freqtrade will download the necessary candle types for regular operation automatically.`,-1)])]),l(`div`,je,[f(W,{modelValue:s(j).customExchange,"onUpdate:modelValue":h[11]||=e=>s(j).customExchange=e,class:`mb-2`},{default:i(()=>[...h[25]||=[g(` Custom Exchange `,-1)]]),_:1},8,[`modelValue`]),f(D,{name:`fade`},{default:i(()=>[e(f(Z,{modelValue:s(j).selectedExchange,"onUpdate:modelValue":h[12]||=e=>s(j).selectedExchange=e},null,8,[`modelValue`]),[[O,s(j).customExchange]])]),_:1})])],512),[[O,s(F)]])]),_:1})]),l(`div`,Me,[f(w,{severity:`primary`,onClick:U},{default:i(()=>[...h[26]||=[g(`Start Download`,-1)]]),_:1})])])])]),_:1})])}}}),Pe={};function Fe(e,t){let n=Ne;return r(),m(n,{class:`pt-4`})}var Ie=I(Pe,[[`render`,Fe]]);export{Ie as default};
//# sourceMappingURL=DownloadDataView-DHM1xo28.js.map