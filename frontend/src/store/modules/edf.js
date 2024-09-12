import { defineStore } from "pinia";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { listEdf } from "@/api/system/edf";

export const useEDFStore = defineStore('EDF', () => {
  const { proxy } = getCurrentInstance();
  const edfList = ref([]);
  const loading = ref('false')
  const queryParams=reactive( {
    pageNum: 1,
    pageSize: 10,
    edfName: undefined,
    edfSfreq: undefined,
    uploadBy: undefined,
    uploadTime: undefined,
  })
  const edfListWithCount = computed(()=>
    edfList.value.map((item)=>({
      ...item,
      validChannelsCount:item.validChannels?item.validChannels.split(",").length:0
    }))
  )

  onMounted(()=>{
    refreshListEDF();
  })

  const refreshListEDF=()=>{
    loading.value=true;
    listEdf(proxy.addDateRange(queryParams, [])).then(
      (res) => {
        loading.value=false;
        edfList.value = res.rows;
      }
    );
  }



  return { edfListWithCount,refreshListEDF }
})